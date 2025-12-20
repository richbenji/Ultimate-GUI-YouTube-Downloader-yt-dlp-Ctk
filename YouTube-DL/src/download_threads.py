# src/download_threads.py
import os
import threading
import yt_dlp
from .video_info import VideoInfo
from .translations import get_text

# ------------ Exception spéciale pour une annulation propre ------------
class DownloadCancelled(Exception):
    """Exception interne utilisée pour signaler une annulation propre."""
    pass


# =========================== INFO THREAD ===============================
class InfoThread(threading.Thread):
    """
    Thread chargé UNIQUEMENT de récupérer les infos d'une vidéo.
    L'URL est supposée valide (déjà vérifiée par resolve_url).
    """

    def __init__(self, url, app, callback=None, error_callback=None):
        super().__init__()
        self.url = url
        self.app = app
        self.callback = callback
        self.error_callback = error_callback
        self.daemon = True

    def run(self):
        try:
            info = VideoInfo(self.url)
            info.fetch_info()

            if self.callback:
                self.callback(info)

        except Exception:
            # Erreur technique uniquement (yt-dlp, réseau, etc.)
            if self.error_callback:
                self.error_callback(
                    get_text("fetching_impossible", self.app.current_language)
                )

# ======================== DOWNLOAD THREAD =============================
class DownloadThread(threading.Thread):
    def __init__(self, url, app, download_type, resolution, bitrate, audio_format, output_path,
                 progress_callback=None, status_callback=None, finished_callback=None):
        """
        Thread qui télécharge soit :
            - une vidéo + audio (download_type = 'video')
            - un fichier audio seul (download_type = 'audio')

        progress_callback  : fonction appelée à chaque mise à jour du pourcentage
        status_callback    : fonction appelée pour afficher un texte de statut (vitesse, ETA…)
        finished_callback  : fonction appelée lorsqu'un téléchargement se termine
        """

        super().__init__()
        self.url = url
        self.app = app
        self.download_type = download_type
        self.resolution = resolution
        self.bitrate = bitrate
        self.audio_format = audio_format
        self.output_path = output_path

        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.finished_callback = finished_callback

        # Permet d'annuler un téléchargement proprement
        self.is_cancelled = False
        self.daemon = True

    # ----- Hook de progression -----
    def progress_hook(self, d):
        """
         d est un dictionnaire envoyé directement par yt-dlp.
         Il contient :
             - d["status"]       -> "downloading" ou "finished"
             - d["_percent_str"] -> "32.1%"
             - d["_speed_str"]   -> "1.2MiB/s"
             - d["_eta_str"]     -> "00:12"
         """

        # Gestion de l'annulation
        if self.is_cancelled:
            # On arrête proprement le téléchargement
            raise DownloadCancelled()

        status = d.get('status', '')
        if status == 'downloading':
            # Pourcentage brut envoyé à la barre de progression
            pct_str = d.get('_percent_str', '0%').replace('%', '').strip()
            try:
                pct = float(pct_str)
            except Exception:
                pct = 0.0

            if self.progress_callback:
                self.progress_callback(int(pct))

            if self.status_callback:
                self.status_callback(
                    f"{get_text('downloading', self.app.current_language)} "
                    f"{d.get('_speed_str', '')} - "
                    f"{get_text('remaining_time', self.app.current_language)} {d.get('_eta_str', '')}"  # temps restant
                )

        elif status == 'finished':
            # Quand yt-dlp a tout téléchargé
            if self.progress_callback:
                self.progress_callback(100)
            if self.status_callback:
                self.status_callback(get_text("processing_file", self.app.current_language))

    # ----- Exécution -----
    def run(self):
        try:
            # ---------- Construction des options yt-dlp ----------

            # ----- VIDEO + AUDIO -----

            if self.download_type == "video":

                # Nettoyage "1080p" -> "1080"
                if self.resolution is None:
                    height = None
                else:
                    height = self.resolution[:-1]

                # Format vidéo : télécharge directement à la résolution demandée
                if height:
                    format_str = f'bestvideo[height<={height}][ext=mp4]'
                else:
                    format_str = f'bestvideo[ext=mp4]'

                # Audio : si bitrate choisi par l'utilisateur
                if self.bitrate is None:
                    # Best audio (AAC / m4a de préférence)
                    format_str += '+bestaudio[ext=m4a]/bestaudio'
                else:
                    bitrate_val = int(self.bitrate.replace(" kbps", ""))
                    low = bitrate_val - 10
                    high = bitrate_val + 10

                    format_str += (  # += AJOUTE à format_str
                        f'+bestaudio[abr>={low}][abr<={high}][ext=m4a]'
                        f'/bestaudio[ext=m4a]'
                    )

                ydl_opts = {
                    'format': format_str + '/best',
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],  # permet de suivre l'avancement du téléchargement
                    'quiet': True,
                    'no_warnings': True,
                    'merge_output_format': 'mp4',
                    'nooverwrites': True  # évite d'écraser accidentellement des fichiers existants
                }

            # ----- AUDIO ONLY -----

            else:

                # ----- M4A (pas de conversion) -----
                if self.audio_format == "m4a":

                    if self.bitrate is None:
                        audio_format = 'bestaudio[ext=m4a]'
                    else:
                        br = int(self.bitrate.replace(" kbps", ""))
                        audio_format = (
                            f'bestaudio[abr>={br - 10}][abr<={br + 10}][ext=m4a]'
                            f'/bestaudio[ext=m4a]'
                        )

                    ydl_opts = {
                        'format': audio_format,
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self.progress_hook],
                        'quiet': True,
                        'no_warnings': True,
                        'nooverwrites': True
                    }

                # ----- MP3 (conversion volontaire) -----
                else:
                    preferred_quality = (
                        self.bitrate.replace(" kbps", "") if self.bitrate else '0'
                    )

                    ydl_opts = {
                        'format': 'bestaudio[ext=m4a]/bestaudio',
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self.progress_hook],
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': preferred_quality,
                        }],
                        'quiet': True,
                        'no_warnings': True,
                        'nooverwrites': True
                    }

            # ---------- Téléchargement ----------
            # Lancement réel du téléchargement
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            if self.status_callback:
                self.status_callback(get_text("download_complete", self.app.current_language))

            if self.finished_callback:
                self.finished_callback(True)

        # -------- Annulation propre --------
        except DownloadCancelled:
            if self.status_callback:
                self.status_callback(get_text("download_canceled", self.app.current_language))
            if self.finished_callback:
                self.finished_callback(False)

        # -------- Erreur réelle --------
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"{get_text('error_prefix', self.app.current_language)} {e}")
            if self.finished_callback:
                self.finished_callback(False)

    def cancel(self):
        self.is_cancelled = True



# ========================= BATCH DOWNLOAD THREAD ========================
class BatchDownloadThread(threading.Thread):
    def __init__(self, urls, app, download_type, resolution, bitrate, output_path,
                 progress_callback=None, status_callback=None, finished_callback=None):
        super().__init__()
        self.urls = urls
        self.app = app
        self.download_type = download_type
        self.resolution = resolution
        self.bitrate = bitrate
        self.output_path = output_path
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.finished_callback = finished_callback
        self.is_cancelled = False
        self.daemon = True
        self._total_urls = max(1, len(urls))

    # ----- Hook fabriqué pour chaque fichier -----
    def _progress_hook_factory(self, base_percent):
        def hook(d):
            if self.is_cancelled:
                raise DownloadCancelled()

            status = d.get('status', '')
            if status == 'downloading':
                pct_str = d.get('_percent_str', '0%').replace('%', '').strip()
                try:
                    pct = float(pct_str)
                except Exception:
                    pct = 0.0

                total_pct = base_percent + (pct / self._total_urls)

                if self.progress_callback:
                    self.progress_callback(int(total_pct))

                if self.status_callback:
                    fname = d.get('filename', '').split('/')[-1]
                    self.status_callback(f"{fname} - {d.get('_speed_str', '')} - {d.get('_eta_str', '')}")

            elif status == 'finished':
                if self.progress_callback:
                    self.progress_callback(int(base_percent + (100 / self._total_urls)))

        return hook

    # ----- Exécution -----
    def run(self):
        successful = 0

        try:
            for i, raw_url in enumerate(self.urls):
                if self.is_cancelled:
                    raise DownloadCancelled()

                url = raw_url.strip()
                if not url:
                    continue

                # Info de progression
                if self.status_callback:
                    self.status_callback(
                        f"{get_text('checking_url', self.app.current_language)} ({i+1}/{self._total_urls}) : {url}"
                    )

                base_percent = (i * 100) / self._total_urls

                # ----- Construction des options -----
                if self.download_type == "video":
                    height = self.resolution[:-1] if (self.resolution and self.resolution.endswith('p')) else None
                    format_str = 'bestvideo[ext=mp4]'
                    if height:
                        format_str = f'bestvideo[height<={height}][ext=mp4]'

                    if self.bitrate and self.bitrate != "Best":
                        bitrate_val = self.bitrate.replace(" kbps", "")
                        format_str += f'+bestaudio[abr<={bitrate_val}+10][abr>={bitrate_val}-10]/bestaudio[ext=m4a]'
                    else:
                        format_str += '+bestaudio[ext=m4a]'

                    ydl_opts = {
                        'format': format_str + '/best',
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self._progress_hook_factory(base_percent)],
                        'quiet': True,
                        'no_warnings': True,
                        'merge_output_format': 'mp4'
                    }

                else:
                    preferred_quality = self.bitrate.replace(" kbps", "") if (self.bitrate and self.bitrate != "Best") else "192"

                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self._progress_hook_factory(base_percent)],
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': preferred_quality,
                        }],
                        'quiet': True,
                        'no_warnings': True
                    }

                # ----- Téléchargement -----
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                successful += 1

            # -- Fin par lot --
            if self.progress_callback:
                self.progress_callback(100)

            if self.status_callback:
                self.status_callback(get_text("batch_download_complete", self.app.current_language))

            if self.finished_callback:
                self.finished_callback(True)

        # ----- Annulation propre -----
        except DownloadCancelled:
            if self.status_callback:
                self.status_callback(get_text("canceling_batch_download", self.app.current_language))
            if self.finished_callback:
                self.finished_callback(False)

        # ----- Erreurs réelles -----
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"{get_text('error_prefix', self.app.current_language)} {e}")
            if self.finished_callback:
                self.finished_callback(False)

    def cancel(self):
        self.is_cancelled = True
