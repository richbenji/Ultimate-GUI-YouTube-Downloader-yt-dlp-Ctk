import os
import threading
import time
import sys
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp


class VideoInfo:
    def __init__(self, url):
        self.url = url
        self.title = ""
        self.resolutions = []
        self.duration = 0
        self.thumbnail = ""
        self.formats = []
        self.audio_bitrates = []
        self.is_valid = False

    def fetch_info(self):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

                self.title = info.get('title', 'Unknown Title')
                self.duration = info.get('duration', 0)
                self.thumbnail = info.get('thumbnail', '')
                self.formats = info.get('formats', [])

                # Filtrer pour obtenir uniquement les formats vidéo mp4
                video_formats = [f for f in self.formats
                                if f.get('ext') == 'mp4' and f.get('height') is not None]

                # Obtenir les résolutions disponibles
                resolutions = set()
                for f in video_formats:
                    if f.get('height'):
                        resolutions.add(f"{f['height']}p")

                self.resolutions = sorted(list(resolutions),
                                         key=lambda x: int(x[:-1]) if x[:-1].isdigit() else 0,
                                         reverse=True)

                # Obtenir les bitrates audio disponibles
                audio_formats = [f for f in self.formats if f.get('acodec') != 'none' and f.get('abr')]
                bitrates = set()
                for f in audio_formats:
                    if f.get('abr'):
                        bitrates.add(int(f['abr']))

                self.audio_bitrates = sorted(list(bitrates), reverse=True)

                self.is_valid = True
                return True
        except Exception as e:
            print(f"Erreur lors de l'extraction des informations: {str(e)}")
            return False


class InfoThread(threading.Thread):
    def __init__(self, url, callback, error_callback):
        super().__init__()
        self.url = url
        self.callback = callback
        self.error_callback = error_callback

    def run(self):
        try:
            video_info = VideoInfo(self.url)
            if video_info.fetch_info():
                # Utiliser after pour revenir au thread principal
                if self.callback:
                    self.callback(video_info)
            else:
                if self.error_callback:
                    self.error_callback("Impossible d'obtenir les informations de la vidéo")
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))


class DownloadThread(threading.Thread):
    def __init__(self, url, download_type, resolution, bitrate, output_path, progress_callback, status_callback, finished_callback):
        super().__init__()
        self.url = url
        self.download_type = download_type
        self.resolution = resolution
        self.bitrate = bitrate
        self.output_path = output_path
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.finished_callback = finished_callback
        self.is_cancelled = False

    def progress_hook(self, d):
        if self.is_cancelled:
            raise Exception("Téléchargement annulé")

        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            p = p.replace('%', '').strip()
            try:
                percentage = float(p)
                if self.progress_callback:
                    self.progress_callback(int(percentage))
            except:
                pass

            speed = d.get('_speed_str', '')
            eta = d.get('_eta_str', '')
            if self.status_callback:
                self.status_callback(f"Téléchargement: {speed} - Temps restant: {eta}")

        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback(100)
            if self.status_callback:
                self.status_callback("Traitement du fichier...")

    def run(self):
        try:
            if self.download_type == "video":
                height = int(self.resolution[:-1])  # Enlever le 'p' et convertir en int

                format_str = f'bestvideo[height<={height}][ext=mp4]'

                # Si un bitrate spécifique est sélectionné
                if self.bitrate and self.bitrate != "Auto":
                    bitrate_val = int(self.bitrate.replace(" kbps", ""))
                    # Trouver le format audio le plus proche du bitrate demandé
                    format_str += f'+bestaudio[abr<={bitrate_val+10}][abr>={bitrate_val-10}]/bestaudio[ext=m4a]'
                else:
                    format_str += '+bestaudio[ext=m4a]'

                # Fallback options
                format_str += f'/best[height<={height}][ext=mp4]/best'

                ydl_opts = {
                    'format': format_str,
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                    'merge_output_format': 'mp4'
                }
            else:  # audio
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': self.bitrate.replace(" kbps", "") if self.bitrate and self.bitrate != "Auto" else "192",
                    }],
                    'quiet': True,
                    'no_warnings': True,
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            if self.status_callback:
                self.status_callback(f"Téléchargement terminé")
            if self.finished_callback:
                self.finished_callback(True)
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Erreur: {str(e)}")
            if self.finished_callback:
                self.finished_callback(False)

    def cancel(self):
        self.is_cancelled = True


class BatchDownloadThread(threading.Thread):
    def __init__(self, urls, download_type, resolution, bitrate, output_path, progress_callback, status_callback, finished_callback):
        super().__init__()
        self.urls = urls
        self.download_type = download_type
        self.resolution = resolution
        self.bitrate = bitrate
        self.output_path = output_path
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.finished_callback = finished_callback
        self.current_progress = 0
        self.is_cancelled = False

    def progress_hook(self, d):
        if self.is_cancelled:
            raise Exception("Téléchargement annulé")

        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            p = p.replace('%', '').strip()
            try:
                percentage = float(p)
                # Adapter le pourcentage à l'échelle globale
                url_progress = percentage / len(self.urls)
                total_progress = self.current_progress + url_progress
                if self.progress_callback:
                    self.progress_callback(int(total_progress))
            except:
                pass

            speed = d.get('_speed_str', '')
            eta = d.get('_eta_str', '')
            filename = d.get('filename', '').split('/')[-1] if '/' in d.get('filename', '') else d.get('filename', '').split('\\')[-1]
            if self.status_callback:
                self.status_callback(f"Fichier: {filename} - {speed} - Temps restant: {eta}")

    def run(self):
        total_urls = len(self.urls)
        successful = 0
        failed = 0

        for i, url in enumerate(self.urls):
            if self.is_cancelled:
                if self.status_callback:
                    self.status_callback("Téléchargement annulé")
                if self.finished_callback:
                    self.finished_callback(False)
                return

            self.current_progress = (i / total_urls) * 100

            try:
                url = url.strip()
                if not url:
                    continue

                if self.status_callback:
                    self.status_callback(f"Traitement URL ({i+1}/{total_urls}): {url}")

                if self.download_type == "video":
                    height = int(self.resolution[:-1])  # Enlever le 'p' et convertir en int

                    format_str = f'bestvideo[height<={height}][ext=mp4]'

                    # Si un bitrate spécifique est sélectionné
                    if self.bitrate and self.bitrate != "Auto":
                        bitrate_val = int(self.bitrate.replace(" kbps", ""))
                        # Trouver le format audio le plus proche du bitrate demandé
                        format_str += f'+bestaudio[abr<={bitrate_val+10}][abr>={bitrate_val-10}]/bestaudio[ext=m4a]'
                    else:
                        format_str += '+bestaudio[ext=m4a]'

                    # Fallback options
                    format_str += f'/best[height<={height}][ext=mp4]/best'

                    ydl_opts = {
                        'format': format_str,
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self.progress_hook],
                        'quiet': True,
                        'no_warnings': True,
                        'merge_output_format': 'mp4'
                    }
                else:  # audio
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self.progress_hook],
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': self.bitrate.replace(" kbps", "") if self.bitrate and self.bitrate != "Auto" else "192",
                        }],
                        'quiet': True,
                        'no_warnings': True,
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                successful += 1

            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"Erreur avec {url}: {str(e)}")
                failed += 1

        if self.progress_callback:
            self.progress_callback(100)
        if self.status_callback:
            self.status_callback(f"Téléchargement par lot terminé. {successful}/{total_urls} fichiers téléchargés avec succès.")
        if self.finished_callback:
            self.finished_callback(True)

    def cancel(self):
        self.is_cancelled = True


class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader")
        self.geometry("800x600")

        # Configuration du thème
        ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Thèmes: "blue", "green", "dark-blue"

        # Dossier de sortie par défaut
        self.output_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # Variables pour stocker les threads actifs
        self.info_thread = None
        self.download_thread = None
        self.batch_download_thread = None

        # Variable pour stocker les infos vidéo
        self.current_video_info = None

        # Création de l'interface
        self.setup_ui()

    def setup_ui(self):
        # Création des onglets
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Création des onglets
        self.tab_single = self.tabview.add("Téléchargement unique")
        self.tab_batch = self.tabview.add("Téléchargement par lot")

        self.setup_single_download_tab()
        self.setup_batch_download_tab()

    def setup_single_download_tab(self):
        # Frame pour l'URL
        url_frame = ctk.CTkFrame(self.tab_single)
        url_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(url_frame, text="URL YouTube:").pack(side="left", padx=5)
        self.url_input = ctk.CTkEntry(url_frame, width=400, placeholder_text="Collez l'URL YouTube ici")
        self.url_input.pack(side="left", padx=5, fill="x", expand=True)

        self.check_url_btn = ctk.CTkButton(url_frame, text="Vérifier", command=self.check_url)
        self.check_url_btn.pack(side="left", padx=5)

        # Titre de la vidéo
        title_frame = ctk.CTkFrame(self.tab_single)
        title_frame.pack(fill="x", padx=10, pady=5)

        self.title_label = ctk.CTkLabel(title_frame, text="Titre: ", wraplength=700)
        self.title_label.pack(fill="x", padx=10, pady=5)

        # Type de téléchargement (vidéo/audio)
        type_frame = ctk.CTkFrame(self.tab_single)
        type_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(type_frame, text="Type:").pack(side="left", padx=5)

        self.download_type_var = tk.StringVar(value="video")
        self.video_radio = ctk.CTkRadioButton(type_frame, text="Vidéo", variable=self.download_type_var, value="video", command=self.toggle_resolution_options)
        self.video_radio.pack(side="left", padx=10)

        self.audio_radio = ctk.CTkRadioButton(type_frame, text="Audio uniquement", variable=self.download_type_var, value="audio", command=self.toggle_resolution_options)
        self.audio_radio.pack(side="left", padx=10)

        # Résolution (pour les vidéos)
        res_frame = ctk.CTkFrame(self.tab_single)
        res_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(res_frame, text="Résolution:").pack(side="left", padx=5)

        self.resolution_var = tk.StringVar()
        self.resolution_combo = ctk.CTkComboBox(res_frame, variable=self.resolution_var, values=["Choisir une résolution"])
        self.resolution_combo.pack(side="left", padx=5)

        # Bitrate audio
        bitrate_frame = ctk.CTkFrame(self.tab_single)
        bitrate_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(bitrate_frame, text="Bitrate audio:").pack(side="left", padx=5)

        self.bitrate_var = tk.StringVar(value="Auto")
        self.bitrate_combo = ctk.CTkComboBox(bitrate_frame, variable=self.bitrate_var,
                                            values=["Auto", "320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"])
        self.bitrate_combo.pack(side="left", padx=5)

        # Dossier de sortie
        output_frame = ctk.CTkFrame(self.tab_single)
        output_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(output_frame, text="Dossier de sortie:").pack(side="left", padx=5)

        self.output_path_var = tk.StringVar(value=self.output_path)
        self.output_path_entry = ctk.CTkEntry(output_frame, textvariable=self.output_path_var, width=350)
        self.output_path_entry.pack(side="left", padx=5, fill="x", expand=True)

        browse_btn = ctk.CTkButton(output_frame, text="Parcourir", command=self.select_output_folder)
        browse_btn.pack(side="left", padx=5)

        # Boutons Télécharger et Annuler
        buttons_frame = ctk.CTkFrame(self.tab_single)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        self.download_btn = ctk.CTkButton(buttons_frame, text="Télécharger", command=self.start_download, state="disabled")
        self.download_btn.pack(side="left", padx=5)

        self.cancel_btn = ctk.CTkButton(buttons_frame, text="Annuler", command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side="left", padx=5)

        # Barre de progression
        progress_frame = ctk.CTkFrame(self.tab_single)
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)

        # Status
        status_frame = ctk.CTkFrame(self.tab_single)
        status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(status_frame, text="Prêt")
        self.status_label.pack(fill="x", padx=10, pady=5)

    def setup_batch_download_tab(self):
        # Zone de texte pour les URLs
        urls_frame = ctk.CTkFrame(self.tab_batch)
        urls_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(urls_frame, text="Liste des URLs YouTube (une par ligne):").pack(anchor="w", padx=5, pady=5)

        self.urls_text = ctk.CTkTextbox(urls_frame, height=150)
        self.urls_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Type de téléchargement (vidéo/audio)
        type_frame = ctk.CTkFrame(self.tab_batch)
        type_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(type_frame, text="Type:").pack(side="left", padx=5)

        self.batch_download_type_var = tk.StringVar(value="video")
        self.batch_video_radio = ctk.CTkRadioButton(type_frame, text="Vidéo", variable=self.batch_download_type_var, value="video", command=self.toggle_batch_resolution_options)
        self.batch_video_radio.pack(side="left", padx=10)

        self.batch_audio_radio = ctk.CTkRadioButton(type_frame, text="Audio uniquement", variable=self.batch_download_type_var, value="audio", command=self.toggle_batch_resolution_options)
        self.batch_audio_radio.pack(side="left", padx=10)

        # Résolution (pour les vidéos)
        res_frame = ctk.CTkFrame(self.tab_batch)
        res_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(res_frame, text="Résolution:").pack(side="left", padx=5)

        self.batch_resolution_var = tk.StringVar(value="720p")
        self.batch_resolution_combo = ctk.CTkComboBox(res_frame, variable=self.batch_resolution_var,
                                                   values=["1080p", "720p", "480p", "360p", "240p", "144p"])
        self.batch_resolution_combo.pack(side="left", padx=5)

        # Bitrate audio
        bitrate_frame = ctk.CTkFrame(self.tab_batch)
        bitrate_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(bitrate_frame, text="Bitrate audio:").pack(side="left", padx=5)

        self.batch_bitrate_var = tk.StringVar(value="Auto")
        self.batch_bitrate_combo = ctk.CTkComboBox(bitrate_frame, variable=self.batch_bitrate_var,
                                                  values=["Auto", "320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"])
        self.batch_bitrate_combo.pack(side="left", padx=5)

        # Chargement depuis un fichier
        file_frame = ctk.CTkFrame(self.tab_batch)
        file_frame.pack(fill="x", padx=10, pady=5)

        self.load_file_btn = ctk.CTkButton(file_frame, text="Charger une liste depuis un fichier", command=self.load_urls_from_file)
        self.load_file_btn.pack(side="left", padx=5)

        # Dossier de sortie
        output_frame = ctk.CTkFrame(self.tab_batch)
        output_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(output_frame, text="Dossier de sortie:").pack(side="left", padx=5)

        self.batch_output_path_var = tk.StringVar(value=self.output_path)
        self.batch_output_path_entry = ctk.CTkEntry(output_frame, textvariable=self.batch_output_path_var, width=350)
        self.batch_output_path_entry.pack(side="left", padx=5, fill="x", expand=True)

        batch_browse_btn = ctk.CTkButton(output_frame, text="Parcourir", command=self.select_batch_output_folder)
        batch_browse_btn.pack(side="left", padx=5)

        # Boutons Télécharger et Annuler
        buttons_frame = ctk.CTkFrame(self.tab_batch)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        self.batch_download_btn = ctk.CTkButton(buttons_frame, text="Télécharger par lot", command=self.start_batch_download)
        self.batch_download_btn.pack(side="left", padx=5)

        self.batch_cancel_btn = ctk.CTkButton(buttons_frame, text="Annuler", command=self.cancel_batch_download, state="disabled")
        self.batch_cancel_btn.pack(side="left", padx=5)

        # Barre de progression
        progress_frame = ctk.CTkFrame(self.tab_batch)
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.batch_progress_bar = ctk.CTkProgressBar(progress_frame)
        self.batch_progress_bar.pack(fill="x", padx=10, pady=5)
        self.batch_progress_bar.set(0)

        # Status
        status_frame = ctk.CTkFrame(self.tab_batch)
        status_frame.pack(fill="x", padx=10, pady=5)

        self.batch_status_label = ctk.CTkLabel(status_frame, text="Prêt")
        self.batch_status_label.pack(fill="x", padx=10, pady=5)

    def check_url(self):
        url = self.url_input.get().strip()
        if not url:
            self.status_label.configure(text="Veuillez entrer une URL valide")
            return

        self.status_label.configure(text="Vérification de l'URL...")
        self.check_url_btn.configure(state="disabled")

        # Démarrer le thread de vérification
        self.info_thread = InfoThread(
            url=url,
            callback=lambda video_info: self.after(0, lambda: self.on_info_received(video_info)),
            error_callback=lambda error_msg: self.after(0, lambda: self.on_info_error(error_msg))
        )
        self.info_thread.daemon = True
        self.info_thread.start()

    def on_info_received(self, video_info):
        self.current_video_info = video_info
        self.title_label.configure(text=f"Titre: {video_info.title}")

        # Mise à jour du combobox de résolution
        if video_info.resolutions:
            self.resolution_combo.configure(values=video_info.resolutions)
            self.resolution_combo.set(video_info.resolutions[0])
        else:
            default_resolutions = ["1080p", "720p", "480p", "360p", "240p"]
            self.resolution_combo.configure(values=default_resolutions)
            self.resolution_combo.set(default_resolutions[0])

        # Mise à jour du combobox de bitrate
        bitrates = ["Auto"]
        for bitrate in video_info.audio_bitrates:
            bitrates.append(f"{bitrate} kbps")

        if len(bitrates) == 1:  # Seulement "Auto"
            bitrates.extend(["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"])

        self.bitrate_combo.configure(values=bitrates)
        self.bitrate_combo.set("Auto")

        self.status_label.configure(text=f"Vidéo trouvée: {video_info.title}")
        self.download_btn.configure(state="normal")
        self.check_url_btn.configure(state="normal")

    def on_info_error(self, error_message):
        self.status_label.configure(text=f"Erreur: {error_message}")
        self.check_url_btn.configure(state="normal")
        self.download_btn.configure(state="disabled")

    def toggle_resolution_options(self):
        is_video = self.download_type_var.get() == "video"
        if not is_video:
            self.resolution_combo.configure(state="disabled")
        else:
            self.resolution_combo.configure(state="normal")

    def toggle_batch_resolution_options(self):
        is_video = self.batch_download_type_var.get() == "video"
        if not is_video:
            self.batch_resolution_combo.configure(state="disabled")
        else:
            self.batch_resolution_combo.configure(state="normal")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner un dossier de sortie")
        if folder:
            self.output_path = folder
            self.output_path_var.set(folder)
            self.batch_output_path_var.set(folder)  # Synchroniser entre les onglets

    def select_batch_output_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner un dossier de sortie")
        if folder:
            self.output_path = folder
            self.batch_output_path_var.set(folder)
            self.output_path_var.set(folder)  # Synchroniser entre les onglets


    def start_download(self):
        url = self.url_input.get().strip()
        download_type = self.download_type_var.get()

        resolution = ""
        if download_type == "video":
            resolution = self.resolution_var.get()
            if not resolution or resolution == "Choisir une résolution":
                self.status_label.configure(text="Veuillez sélectionner une résolution")
                return

        bitrate = self.bitrate_var.get()
        output_path = self.output_path_var.get()

        self.download_thread = DownloadThread(
            url, download_type, resolution, bitrate, output_path,
            lambda value: self.after(0, lambda: self.update_progress(value)),
            lambda text: self.after(0, lambda: self.update_status(text)),
            lambda success: self.after(0, lambda: self.download_finished(success))
        )

        self.download_btn.configure(state="disabled")
        self.check_url_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)

        self.download_thread.daemon = True
        self.download_thread.start()

    def cancel_download(self):
        if self.download_thread:
            self.download_thread.cancel()
            self.status_label.configure(text="Annulation du téléchargement...")
            self.cancel_btn.configure(state="disabled")

    def load_urls_from_file(self):
        file_path = filedialog.askopenfilename(title="Charger une liste d'URLs", filetypes=[("Fichiers texte", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    urls = file.readlines()
                self.urls_text.delete("0.0", "end")
                self.urls_text.insert("0.0", ''.join(urls))
                self.batch_status_label.configure(text=f"Chargé {len(urls)} URLs depuis le fichier")
            except Exception as e:
                self.batch_status_label.configure(text=f"Erreur lors du chargement du fichier: {str(e)}")

    def start_batch_download(self):
        urls_text = self.urls_text.get("0.0", "end").strip()
        if not urls_text:
            self.batch_status_label.configure(text="Veuillez ajouter au moins une URL")
            return

        urls = urls_text.split('\n')
        urls = [url.strip() for url in urls if url.strip()]

        if not urls:
            self.batch_status_label.configure(text="Aucune URL valide trouvée")
            return

        download_type = self.batch_download_type_var.get()
        resolution = ""
        if download_type == "video":
            resolution = self.batch_resolution_var.get()

        bitrate = self.batch_bitrate_var.get()
        output_path = self.batch_output_path_var.get()

        self.batch_download_thread = BatchDownloadThread(
            urls, download_type, resolution, bitrate, output_path,
            lambda value: self.after(0, lambda: self.update_batch_progress(value)),
            lambda text: self.after(0, lambda: self.update_batch_status(text)),
            lambda success: self.after(0, lambda: self.batch_download_finished(success))
        )

        self.batch_download_btn.configure(state="disabled")
        self.load_file_btn.configure(state="disabled")
        self.batch_cancel_btn.configure(state="normal")
        self.batch_progress_bar.set(0)

        self.batch_download_thread.daemon = True
        self.batch_download_thread.start()

    def cancel_batch_download(self):
        if self.batch_download_thread:
            self.batch_download_thread.cancel()
            self.batch_status_label.configure(text="Annulation du téléchargement par lot...")
            self.batch_cancel_btn.configure(state="disabled")

    def update_progress(self, value):
        self.progress_bar.set(value / 100)

    def update_status(self, status_text):
        self.status_label.configure(text=status_text)

    def download_finished(self, success):
        self.download_btn.configure(state="normal")
        self.check_url_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

        if success:
            self.progress_bar.set(1)
            messagebox.showinfo("Téléchargement terminé", "Le téléchargement a été complété avec succès!")

    def update_batch_progress(self, value):
        self.batch_progress_bar.set(value / 100)

    def update_batch_status(self, status_text):
        self.batch_status_label.configure(text=status_text)

    def batch_download_finished(self, success):
        self.batch_download_btn.configure(state="normal")
        self.load_file_btn.configure(state="normal")
        self.batch_cancel_btn.configure(state="disabled")

        if success:
            self.batch_progress_bar.set(1)
            messagebox.showinfo("Téléchargement par lot terminé", "Le téléchargement par lot a été complété!")

def main():
    app = YouTubeDownloader()
    app.mainloop()

if __name__ == "__main__":
    main()
