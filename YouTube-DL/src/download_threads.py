# src/download_threads.py
"""Threads de récupération d'info et de téléchargement (single & batch)."""

import os
import threading
import yt_dlp
from .video_info import VideoInfo


class InfoThread(threading.Thread):
    def __init__(self, url, callback=None, error_callback=None):
        super().__init__()
        self.url = url
        self.callback = callback
        self.error_callback = error_callback
        self.daemon = True

    def run(self):
        try:
            info = VideoInfo(self.url)
            if info.fetch_info():
                if self.callback:
                    self.callback(info)
            else:
                if self.error_callback:
                    self.error_callback("Impossible d'obtenir les informations de la vidéo")
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))


class DownloadThread(threading.Thread):
    def __init__(self, url, download_type, resolution, bitrate, output_path,
                 progress_callback=None, status_callback=None, finished_callback=None):
        super().__init__()
        self.url = url
        self.download_type = download_type  # "video" or "audio"
        self.resolution = resolution
        self.bitrate = bitrate
        self.output_path = output_path
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.finished_callback = finished_callback
        self.is_cancelled = False
        self.daemon = True

    def progress_hook(self, d):
        if self.is_cancelled:
            raise Exception("Téléchargement annulé")

        status = d.get('status', '')
        if status == 'downloading':
            pct_str = d.get('_percent_str', '0%').replace('%', '').strip()
            try:
                pct = float(pct_str)
            except Exception:
                pct = 0.0
            if self.progress_callback:
                self.progress_callback(int(pct))
            if self.status_callback:
                self.status_callback(f"Téléchargement: {d.get('_speed_str', '')} - Temps restant: {d.get('_eta_str', '')}")
        elif status == 'finished':
            if self.progress_callback:
                self.progress_callback(100)
            if self.status_callback:
                self.status_callback("Traitement du fichier...")

    def run(self):
        try:
            if self.download_type == "video":
                height = self.resolution[:-1] if self.resolution and self.resolution.endswith('p') else None
                format_str = f'bestvideo[ext=mp4]'
                if height:
                    format_str = f'bestvideo[height<={height}][ext=mp4]'

                if self.bitrate and self.bitrate != "Auto":
                    bitrate_val = self.bitrate.replace(" kbps", "")
                    format_str += f'+bestaudio[abr<={bitrate_val+10}][abr>={bitrate_val-10}]/bestaudio[ext=m4a]'
                else:
                    format_str += '+bestaudio[ext=m4a]'

                format_str += f'/best'  # fallback

                ydl_opts = {
                    'format': format_str,
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                    'merge_output_format': 'mp4'
                }
            else:  # audio
                preferred_quality = self.bitrate.replace(" kbps", "") if (self.bitrate and self.bitrate != "Auto") else "192"
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': preferred_quality,
                    }],
                    'quiet': True,
                    'no_warnings': True,
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            if self.status_callback:
                self.status_callback("Téléchargement terminé")
            if self.finished_callback:
                self.finished_callback(True)

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Erreur: {e}")
            if self.finished_callback:
                self.finished_callback(False)

    def cancel(self):
        self.is_cancelled = True


class BatchDownloadThread(threading.Thread):
    def __init__(self, urls, download_type, resolution, bitrate, output_path,
                 progress_callback=None, status_callback=None, finished_callback=None):
        super().__init__()
        self.urls = urls
        self.download_type = download_type
        self.resolution = resolution
        self.bitrate = bitrate
        self.output_path = output_path
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.finished_callback = finished_callback
        self.is_cancelled = False
        self.daemon = True

        # variables d'état interne
        self._total_urls = max(1, len(self.urls))

    def _progress_hook_factory(self, base_percent):
        """Retourne une closure qui transforme le percent courant en percent global."""
        def hook(d):
            if self.is_cancelled:
                raise Exception("Téléchargement annulé")
            status = d.get('status', '')
            if status == 'downloading':
                pct_str = d.get('_percent_str', '0%').replace('%', '').strip()
                try:
                    pct = float(pct_str)
                except Exception:
                    pct = 0.0
                # base_percent est la part complétée avant ce fichier (0..100)
                total = base_percent + (pct / self._total_urls)
                if self.progress_callback:
                    self.progress_callback(int(total))
                if self.status_callback:
                    filename = d.get('filename', '') or ''
                    filename = filename.split('/')[-1].split('\\')[-1]
                    self.status_callback(f"Fichier: {filename} - {d.get('_speed_str', '')} - Temps restant: {d.get('_eta_str', '')}")
            elif status == 'finished':
                # quand un fichier est fini, on peut pousser la progression du fichier à son maximum local
                if self.progress_callback:
                    self.progress_callback(int(min(100, (base_percent + (100 / self._total_urls)))))
        return hook

    def run(self):
        successful = 0
        failed = 0

        for i, url in enumerate(self.urls):
            if self.is_cancelled:
                if self.status_callback:
                    self.status_callback("Téléchargement annulé")
                if self.finished_callback:
                    self.finished_callback(False)
                return

            url = url.strip()
            if not url:
                continue

            base_percent = (i * 100) / self._total_urls

            try:
                if self.status_callback:
                    self.status_callback(f"Traitement URL ({i+1}/{self._total_urls}): {url}")

                # construire options comme pour DownloadThread
                if self.download_type == "video":
                    height = self.resolution[:-1] if (self.resolution and self.resolution.endswith('p')) else None
                    format_str = 'bestvideo[ext=mp4]'
                    if height:
                        format_str = f'bestvideo[height<={height}][ext=mp4]'
                    if self.bitrate and self.bitrate != "Auto":
                        bitrate_val = self.bitrate.replace(" kbps", "")
                        format_str += f'+bestaudio[abr<={bitrate_val+10}][abr>={bitrate_val-10}]/bestaudio[ext=m4a]'
                    else:
                        format_str += '+bestaudio[ext=m4a]'
                    format_str += '/best'
                    ydl_opts = {
                        'format': format_str,
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self._progress_hook_factory(base_percent)],
                        'quiet': True,
                        'no_warnings': True,
                        'merge_output_format': 'mp4'
                    }
                else:
                    preferred_quality = self.bitrate.replace(" kbps", "") if (self.bitrate and self.bitrate != "Auto") else "192"
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
                        'no_warnings': True,
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                successful += 1

            except Exception as e:
                failed += 1
                if self.status_callback:
                    self.status_callback(f"Erreur avec {url}: {e}")

        # fin de boucle
        if self.progress_callback:
            self.progress_callback(100)
        if self.status_callback:
            self.status_callback(f"Téléchargement par lot terminé. {successful}/{self._total_urls} fichiers téléchargés avec succès.")
        if self.finished_callback:
            self.finished_callback(True)

    def cancel(self):
        self.is_cancelled = True
