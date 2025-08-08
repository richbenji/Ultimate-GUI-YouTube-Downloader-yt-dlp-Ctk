import os
import threading
import time
import sys
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
from PIL import Image, ImageTk
from src.translations import get_text

#TODO : fusionner les refresh_ui et autres pour n'avoir qu'1 seule fonction de traduction

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

        # Langue par défaut
        self.current_language = "fr"  # ou "en" selon votre préférence

        # Langues disponibles avec leurs noms d'affichage
        self.available_languages = {
            "fr": "Français",
            "en": "English",
            "es": "Español",
            "it": "Italiano",
            "de": "Deutsch"
        }

        self.title(get_text("app_title", self.current_language))
        self.geometry("800x700")

        # Configuration du thème
        ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Thèmes: "blue", "green", "dark-blue"

        # Dossier de sortie par défaut
        self.output_path = os.path.join(os.path.expanduser("~"), "Téléchargements")

        # Variables pour stocker les threads actifs
        self.info_thread = None
        self.download_thread = None
        self.batch_download_thread = None

        # Variable pour stocker les infos vidéo
        self.current_video_info = None

        # Création de l'interface
        self.setup_ui()

    def change_language(self, selected_language_name):
        """Change la langue en fonction du nom sélectionné"""
        # Trouver le code de langue correspondant au nom
        for lang_code, lang_name in self.available_languages.items():
            if lang_name == selected_language_name:
                if self.current_language != lang_code:
                    self.current_language = lang_code
                    self.refresh_ui()
                break

    def refresh_ui(self):
        """Actualise tous les textes de l'interface"""
        # Titre de la fenêtre
        self.title(get_text("app_title", self.current_language))

        # Rafraîchir l'en-tête
        self.title_label_main.configure(text=get_text("app_title", self.current_language))
        self.subtitle_label_main.configure(text=get_text("app_subtitle", self.current_language))

        # Mettre à jour le sélecteur de langue
        current_lang_name = self.available_languages[self.current_language]
        self.language_combo.set(current_lang_name)


        # Au lieu de recréer les onglets, mettre à jour seulement les textes des éléments
        self.refresh_single_tab_texts()
        self.refresh_batch_tab_texts()

    def refresh_single_tab_texts(self):
        """Met à jour les textes de l'onglet de téléchargement unique"""
    # Ici vous mettriez à jour tous les labels et boutons avec get_text()
    # Par exemple :
        self.check_url_btn.configure(text=get_text("check_button", self.current_language))
        self.download_btn.configure(text=get_text("download_button", self.current_language))
    # etc.
        pass


    def refresh_batch_tab_texts(self):
        """Met à jour les textes de l'onglet de téléchargement par lot"""
    # Même principe pour l'onglet batch
        pass

    def load_custom_font(self):
        """Charge la police personnalisée avec CustomTkinter FontManager"""
        try:
            font_path = "/media/richard/PROGRAMMATION/Projets/Ultimate-GUI-YouTube-Downloader-yt-dlp-CtK/YouTube-DL/fonts/TradeGothic Bold.ttf"
            if os.path.exists(font_path):
                # Charger la police avec CustomTkinter FontManager
                ctk.FontManager.load_font(font_path)
                return ctk.CTkFont(family="TradeGothic", size=28, weight="bold")
            else:
                # Police de fallback si le fichier n'existe pas
                return ctk.CTkFont(family="Arial", size=28, weight="bold")
        except Exception as e:
            print(f"Erreur lors du chargement de la police: {e}")
            # Police de fallback en cas d'erreur
            return ctk.CTkFont(family="Arial", size=28, weight="bold")

    def load_logo_image(self):
        """Charge et redimensionne l'image du logo"""
        try:
            logo_path = "/media/richard/PROGRAMMATION/Projets/Ultimate-GUI-YouTube-Downloader-yt-dlp-CtK/YouTube-DL/assets/Youtube_logo.png"
            if os.path.exists(logo_path):
                # Charger l'image avec PIL
                pil_image = Image.open(logo_path)
                # Redimensionner l'image (ajustez la taille selon vos besoins)
                pil_image = pil_image.resize((80, 60), Image.Resampling.LANCZOS)
                # Convertir en CTkImage
                return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(80, 60))
            else:
                return None
        except Exception as e:
            print(f"Erreur lors du chargement du logo: {e}")
            return None

    def setup_ui(self):
        # En-tête
        self.setup_header()

        # Zone principale avec onglets
        self.setup_tabs()

    def setup_header(self):
        """Crée l'en-tête avec logo, titre et sous-titre"""
        # Frame principal pour l'en-tête
        header_frame = ctk.CTkFrame(self, height=120)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)  # Maintient la hauteur fixe

        # Charger le logo
        logo_image = self.load_logo_image()

        # Frame pour le sélecteur de langue (à gauche)
        language_frame = ctk.CTkFrame(header_frame, width=140)
        language_frame.pack(side="left", padx=10, pady=10)
        language_frame.pack_propagate(False)

        # Label pour le sélecteur de langue
        language_label = ctk.CTkLabel(language_frame, text="🌐", font=ctk.CTkFont(size=16))
        language_label.pack(pady=(5, 0))

        # Sélecteur de langue
        language_values = list(self.available_languages.values())
        current_lang_name = self.available_languages[self.current_language]  #TODO : en double dans le code

        self.language_combo = ctk.CTkComboBox(
            master=language_frame,
            values=language_values,
            command=self.change_language,
            width=120,
            height=28
        )
        self.language_combo.set(current_lang_name)  #TODO : en double dans le code
        self.language_combo.pack(pady=(0, 5))

        # Frame pour le logo (à droite)
        if logo_image:
            logo_frame = ctk.CTkFrame(header_frame, width=100, height=100)
            logo_frame.pack(side="right", padx=10, pady=10)
            logo_frame.pack_propagate(False)

            logo_label = ctk.CTkLabel(logo_frame, image=logo_image, text="")
            logo_label.pack(expand=True)

        # Frame pour le titre et sous-titre (au centre)
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Titre principal
        title_font = self.load_custom_font()
        self.title_label_main = ctk.CTkLabel(
            title_frame,
            text=get_text("app_title", self.current_language),
            font=title_font,
            text_color=("#1f538d", "#14375e"),  # Couleur bleue adaptée au thème
            pady = 5
        )
        self.title_label_main.pack(expand=True, pady=(0, 0))

        # Sous-titre
        self.subtitle_label_main = ctk.CTkLabel(
            title_frame,
            text=get_text("app_subtitle", self.current_language),
            font=ctk.CTkFont(family="Arial", size=14, slant="italic"),
            text_color=("#666666", "#999999")  # Couleur plus subtile
        )
        self.subtitle_label_main.pack(expand=True, pady=(0, 0))

    def setup_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_single = self.tabview.add(get_text("single_download_tab", self.current_language))
        self.tab_batch = self.tabview.add(get_text("batch_download_tab", self.current_language))

        self.setup_single_download_tab()
        self.setup_batch_download_tab()

    def setup_single_download_tab(self):
        # Frame pour l'URL
        url_frame = ctk.CTkFrame(self.tab_single)
        url_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(url_frame, text="URL YouTube:").pack(side="left", padx=5)
        self.url_input = ctk.CTkEntry(url_frame, width=400, placeholder_text="Collez l'URL YouTube ici")
        self.url_input.pack(side="left", padx=5, fill="x", expand=True)

        self.check_url_btn = ctk.CTkButton(url_frame, text=get_text("check_button", self.current_language), command=self.check_url)
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
        self.video_radio = ctk.CTkRadioButton(type_frame, text="Vidéo", variable=self.download_type_var, value="video",
                                              command=self.toggle_resolution_options)
        self.video_radio.pack(side="left", padx=10)

        self.audio_radio = ctk.CTkRadioButton(type_frame, text="Audio uniquement", variable=self.download_type_var,
                                              value="audio", command=self.toggle_resolution_options)
        self.audio_radio.pack(side="left", padx=10)

        # Résolution (pour les vidéos)
        res_frame = ctk.CTkFrame(self.tab_single)
        res_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(res_frame, text="Résolution:").pack(side="left", padx=5)

        self.resolution_var = tk.StringVar()
        self.resolution_combo = ctk.CTkComboBox(res_frame, variable=self.resolution_var,
                                                values=["Choisir une résolution"])
        self.resolution_combo.pack(side="left", padx=5)

        # Bitrate audio
        bitrate_frame = ctk.CTkFrame(self.tab_single)
        bitrate_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(bitrate_frame, text="Bitrate audio:").pack(side="left", padx=5)

        self.bitrate_var = tk.StringVar(value="Auto")
        self.bitrate_combo = ctk.CTkComboBox(bitrate_frame, variable=self.bitrate_var,
                                             values=["Auto", "320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps",
                                                     "64 kbps"])
        self.bitrate_combo.pack(side="left", padx=5)

        # Éléments communs (dossier de sortie, boutons, progression, status)
        self.setup_download_controls(self.tab_single, "single")

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
        self.batch_video_radio = ctk.CTkRadioButton(type_frame, text="Vidéo", variable=self.batch_download_type_var,
                                                    value="video", command=self.toggle_batch_resolution_options)
        self.batch_video_radio.pack(side="left", padx=10)

        self.batch_audio_radio = ctk.CTkRadioButton(type_frame, text="Audio uniquement",
                                                    variable=self.batch_download_type_var, value="audio",
                                                    command=self.toggle_batch_resolution_options)
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
                                                   values=["Auto", "320 kbps", "256 kbps", "192 kbps", "128 kbps",
                                                           "96 kbps", "64 kbps"])
        self.batch_bitrate_combo.pack(side="left", padx=5)

        # Chargement depuis un fichier
        file_frame = ctk.CTkFrame(self.tab_batch)
        file_frame.pack(fill="x", padx=10, pady=5)

        self.load_file_btn = ctk.CTkButton(file_frame, text="Charger une liste depuis un fichier",
                                           command=self.load_urls_from_file)
        self.load_file_btn.pack(side="left", padx=5)

        # Éléments communs (dossier de sortie, boutons, progression, status)
        self.setup_download_controls(self.tab_batch, "batch")

    def setup_download_controls(self, parent_tab, tab_type):
        """
        Crée les éléments communs aux deux onglets : dossier de sortie, boutons, progression et status

        Args:
            parent_tab: L'onglet parent (self.tab_single ou self.tab_batch)
            tab_type: "single" ou "batch" pour différencier les variables et commandes
        """

        # Dossier de sortie
        output_frame = ctk.CTkFrame(parent_tab)
        output_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(output_frame, text="Dossier de sortie:").pack(side="left", padx=5)

        # Variables et widgets spécifiques selon le type d'onglet
        if tab_type == "single":
            self.output_path_var = tk.StringVar(value=self.output_path)
            self.output_path_entry = ctk.CTkEntry(output_frame, textvariable=self.output_path_var, width=350)
            browse_command = self.select_output_folder
        else:  # batch
            self.batch_output_path_var = tk.StringVar(value=self.output_path)
            self.output_path_entry = ctk.CTkEntry(output_frame, textvariable=self.batch_output_path_var, width=350)
            browse_command = self.select_batch_output_folder

        self.output_path_entry.pack(side="left", padx=5, fill="x", expand=True)

        browse_btn = ctk.CTkButton(output_frame, text="Parcourir", command=browse_command)
        browse_btn.pack(side="left", padx=5)

        # Boutons Télécharger et Annuler
        buttons_frame = ctk.CTkFrame(parent_tab)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        if tab_type == "single":
            download_text = get_text("download_button", self.current_language)
            download_command = self.start_download
            cancel_command = self.cancel_download
            download_state = "disabled"

            self.download_btn = ctk.CTkButton(buttons_frame, text=download_text,
                                              command=download_command, state=download_state)
            self.download_btn.pack(side="left", padx=5)

            self.cancel_btn = ctk.CTkButton(buttons_frame, text="Annuler",
                                            command=cancel_command, state="disabled")
            self.cancel_btn.pack(side="left", padx=5)

        else:  # batch
            download_text = "Télécharger"
            download_command = self.start_batch_download
            cancel_command = self.cancel_batch_download

            self.batch_download_btn = ctk.CTkButton(buttons_frame, text=download_text,
                                                    command=download_command)
            self.batch_download_btn.pack(side="left", padx=5)

            self.batch_cancel_btn = ctk.CTkButton(buttons_frame, text="Annuler",
                                                  command=cancel_command, state="disabled")
            self.batch_cancel_btn.pack(side="left", padx=5)

        # Barre de progression
        progress_frame = ctk.CTkFrame(parent_tab)
        progress_frame.pack(fill="x", padx=10, pady=5)

        if tab_type == "single":
            self.progress_bar = ctk.CTkProgressBar(progress_frame)
            self.progress_bar.pack(fill="x", padx=10, pady=5)
            self.progress_bar.set(0)
        else:  # batch
            self.batch_progress_bar = ctk.CTkProgressBar(progress_frame)
            self.batch_progress_bar.pack(fill="x", padx=10, pady=5)
            self.batch_progress_bar.set(0)

        # Status
        status_frame = ctk.CTkFrame(parent_tab)
        status_frame.pack(fill="x", padx=10, pady=5)

        if tab_type == "single":
            self.status_label = ctk.CTkLabel(status_frame, text="Prêt")
            self.status_label.pack(fill="x", padx=10, pady=5)
        else:  # batch
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
            # En fait les lignes suivantes ne servent pas car le bouton de téléchargement est grisé par défaut
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
