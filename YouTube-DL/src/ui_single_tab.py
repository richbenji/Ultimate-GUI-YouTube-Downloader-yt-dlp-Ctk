import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk
from .translations import get_text
from .download_threads import InfoThread, DownloadThread
from .utils import ask_output_folder


import threading
from io import BytesIO

# optional imports for thumbnail; handled gracefully if absent
try:
    import requests
    from PIL import Image, UnidentifiedImageError
except Exception:
    requests = None
    Image = None
    UnidentifiedImageError = Exception

class VideoItemFrame(ctk.CTkFrame):
    """Une carte représentant une vidéo ajoutée avec sa miniature, ses options et ses infos."""

    def __init__(self, parent, app, info, parent_tab):
        super().__init__(
            parent,
            corner_radius=10,
            fg_color=("gray80", "gray12"),
            #fg_color=ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"],  # couleurs issues du thème
            #border_color=("gray70", "gray30"),
            #border_width=1
        )

        self.app = app
        self.info = info
        self.parent_tab = parent_tab  # référence vers SingleDownloadTab
        self.original_thumbnail = None  # Stocke l'image PIL originale

        # ---------------- Variables ----------------
        self.download_type = tk.StringVar(value="video")

        if getattr(info, "resolutions", []):
            self.resolution = tk.StringVar(value="Best")
        else:
            self.resolution = tk.StringVar(
                value=get_text("no_resolutions_found", app.current_language)
            )

        if getattr(info, "audio_bitrates", []):
            self.bitrate = tk.StringVar(value="Best")
        else:
            self.bitrate = tk.StringVar(
                value=get_text("no_bitrates_found", app.current_language)
            )

        # ---------------- UI ----------------
        self.audio_format = tk.StringVar(value="m4a")

        # layout principal : 2 colonnes (0 = miniature, 1 = contenu)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        # on garde une seule ligne principale, la miniature occupera plusieurs "rows" visuellement
        # (la grille ci-dessous pour right_frame gérera la verticalité interne)

        # Configuration de la ligne pour permettre l'expansion verticale
        self.grid_rowconfigure(0, weight=0)  # La ligne principale prend tout l'espace


        # --- Colonne gauche : miniature (placeholder d'abord) ---
        self.thumb_label = ctk.CTkLabel(self, text="")
        # rowspan=3 pour que la miniature s'étende visuellement sur la hauteur des 3 sections du right_frame
        self.thumb_label.grid(row=0, column=0, rowspan=3, sticky="ns", padx=10, pady=10)
        if getattr(info, "thumbnail", None):
            self._load_thumbnail_async(info.thumbnail)

        # --- Colonne droite : right_frame (strictement en grid) ---
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=0)

        # configuration interne de right_frame : 3 lignes (titre, options, extra_info)
        right_frame.grid_columnconfigure(0, weight=1)  # colonne texte principale
        right_frame.grid_columnconfigure(1, weight=0)  # colonne petits boutons si besoin
        right_frame.grid_rowconfigure(0, weight=0)  # titre (hauteur minimale)
        right_frame.grid_rowconfigure(1, weight=1)  # options (prend l'espace restant si besoin)
        right_frame.grid_rowconfigure(2, weight=0)  # extra_info (bas)

        # --- Ligne 0 : titre à gauche + boutons (info/close) à droite sur la même ligne ---
        # Titre (col 0)
        self.title_label = ctk.CTkLabel(
            right_frame,
            text=getattr(info, "title", "Titre inconnu"),
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=400,
            justify="left",
            anchor="w"
        )
        self.title_label.grid(row=0, column=0, sticky="nw", padx=(0, 6), pady=(2, 2))

        # Boutons (col 1) — conteneur minimal, on peut pack dedans
        buttons_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        buttons_frame.grid(row=0, column=1, sticky="ne", padx=(0, 0), pady=(2, 2))

        # Info button
        self.info_btn = ctk.CTkButton(
            buttons_frame,
            text="ℹ️",
            width=26, height=26,
            fg_color="transparent",
            hover_color="gray",
            command=self.show_info
        )
        self.info_btn.pack(side="right", padx=(4, 2))

        # Close button
        self.close_btn = ctk.CTkButton(
            buttons_frame,
            text="❌",
            width=26, height=26,
            fg_color="transparent",
            hover_color="red",
            command=lambda: self.parent_tab.remove_video(self)
        )
        self.close_btn.pack(side="right", padx=(2, 0))

        # --- Ligne 1 : container pour les options (type / résolution / bitrate) ---
        opts_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        opts_container.grid(row=1, column=0, columnspan=2, sticky="nw", padx=(0, 0), pady=(4, 0))
        # On utilise pack dans ce sous-conteneur pour empiler verticalement les lignes d'options
        # Type (vidéo / audio)
        type_frame = ctk.CTkFrame(opts_container, fg_color="transparent")
        type_frame.pack(fill="x", pady=(0, 6))
        self.radio_video = ctk.CTkRadioButton(
            type_frame,
            text=get_text("video_option", app.current_language),
            variable=self.download_type,
            value="video")
        self.radio_video.pack(side="left", padx=6)

        self.radio_audio = ctk.CTkRadioButton(
            type_frame,
            text=get_text("audio_only_option", app.current_language),
            variable=self.download_type,
            value="audio")
        self.radio_audio.pack(side="left", padx=6)

        # Résolution
        res_frame = ctk.CTkFrame(opts_container, fg_color="transparent")
        res_frame.pack(fill="x", pady=(0, 6))
        self.resolution_label = ctk.CTkLabel(res_frame,
                                             text=get_text("resolution_label", app.current_language))
        self.resolution_label.pack(side="left", padx=6)
        resolutions = getattr(info, "resolutions", None)
        resolutions_values = ["Best"] + resolutions
        self.resolution_combo = ctk.CTkComboBox(res_frame, variable=self.resolution, values=resolutions_values)
        self.resolution_combo.set(self.resolution.get())
        self.resolution_combo.pack(side="left", padx=6)

        # Bitrate
        br_frame = ctk.CTkFrame(opts_container, fg_color="transparent")
        br_frame.pack(fill="x", pady=(0, 6))

        # Bitrate (à gauche)
        self.bitrate_label = ctk.CTkLabel(br_frame, text=get_text("audio_bitrate_label", app.current_language))
        self.bitrate_label.pack(side="left", padx=6)
        bitrates = getattr(info, "audio_bitrates", None)
        bitrate_values = ["Best"] + [f"{int(b)} kbps" for b in bitrates]
        self.bitrate_combo = ctk.CTkComboBox(br_frame, variable=self.bitrate, values=bitrate_values)
        # default = Best
        self.bitrate_combo.set(self.bitrate.get() or "Best")
        self.bitrate_combo.pack(side="left", padx=6)

        # Format audio (à droite sur la même ligne ; uniquement pour Audio only)
        self.audio_format_label = ctk.CTkLabel(
            br_frame,
            text=get_text("audio_format_label", app.current_language)
        )
        self.audio_format_label.pack(side="left", padx=(20, 6))  # 20px d'espace à gauche pour séparer

        self.audio_format_combo = ctk.CTkComboBox(
            br_frame,
            variable=self.audio_format,
            values=["m4a", "mp3"],
            width=100
        )
        self.audio_format_combo.pack(side="left", padx=6)

        self.resolution_combo.configure(command=lambda _: self.refresh_size_display())
        self.bitrate_combo.configure(command=lambda _: self.refresh_size_display())

        self.download_type.trace_add("write", lambda *_: self.refresh_size_display())

        self.after(200, self.refresh_size_display)  # init

        def _update_ui_for_download_type(*_):
            """Active/désactive les options selon le type de téléchargement."""
            if self.download_type.get() == "video":
                # Mode VIDÉO : résolution active, format audio grisé
                self.resolution_combo.configure(state="normal")
                self.audio_format_combo.configure(state="disabled")
            else:
                # Mode AUDIO : résolution grisée, format audio actif
                self.resolution_combo.configure(state="disabled")
                self.audio_format_combo.configure(state="normal")

        # Lier au changement du radio button Video / Audio
        self.download_type.trace_add("write", _update_ui_for_download_type)

        # Appel initial pour synchroniser l'état au démarrage
        _update_ui_for_download_type()

        # --- Ligne 2 : durée + taille alignées à droite en bas ---
        duration_str = self._format_duration(getattr(info, "duration", 0))
        size_str = self._get_size_string(info)
        self.extra_info_label = ctk.CTkLabel(
            right_frame,
            text=f"⏱ {duration_str}   |   💾 {size_str}",
            font=ctk.CTkFont(size=12, slant="roman"),
            anchor="e",
            justify="right"
        )
        # placer en bas à droite : row=2, col=0 col-span pour couvrir largeur, sticky sud-est
        self.extra_info_label.grid(row=2, column=0, columnspan=2, sticky="se", padx=(0, 0), pady=(6, 4))

        # Attendre que le layout soit calculé, puis redimensionner la miniature
        self.after(100, self._initial_resize)

    # ------------------ Méthodes utilitaires ------------------ #
    def _initial_resize(self):
        """Redimensionne la miniature après que le layout initial soit calculé."""
        if self.original_thumbnail:
            self._resize_thumbnail()

    def _resize_thumbnail(self):
        """Redimensionne la miniature pour s'adapter à la hauteur de la frame (limitée par le texte)."""
        if not self.original_thumbnail:
            return

        # Forcer la mise à jour du layout pour obtenir la vraie hauteur
        self.update_idletasks()

        # Obtenir la hauteur réelle de la frame (déterminée par le contenu texte)
        frame_height = self.winfo_height()

        # Si la hauteur n'est pas encore calculée (valeur 1), réessayer plus tard
        if frame_height <= 1:
            self.after(50, self._resize_thumbnail)
            return

        # Calculer la hauteur disponible pour la miniature (frame_height - padding)
        available_height = frame_height - 20  # -20 pour les pady (10*2)

        # Limiter à une hauteur minimale
        available_height = max(available_height, 50)

        # Calculer les dimensions en conservant le ratio
        img = self.original_thumbnail.copy()
        img_ratio = img.width / img.height

        new_height = available_height
        new_width = int(new_height * img_ratio)

        # Limiter la largeur si nécessaire
        max_width = 300
        if new_width > max_width:
            new_width = max_width
            new_height = int(new_width / img_ratio)

        # Redimensionner l'image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized,
                               size=(new_width, new_height))

        self.thumb_label.configure(image=ctk_img, text="")
        self.thumb_label.image = ctk_img

    def _load_thumbnail_async(self, url):
        """Télécharge la miniature en arrière-plan puis l'affiche."""
        if requests is None or Image is None:
            return

        def worker():
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content)).convert("RGB")
                    self.original_thumbnail = img  # Garde l'original en haute qualité
                    self.app.after(0, self._resize_thumbnail)  # Redimensionne après chargement
            except Exception as e:
                print(f"Erreur miniature {url} : {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _set_thumbnail(self, ctk_img):
        self.thumb_label.configure(image=ctk_img, text="")
        self.thumb_label.image = ctk_img

    def _get_size_string(self, info):
        if not info.formats:
            return "Inconnue"
        sizes = [f.get("filesize") or f.get("filesize_approx") for f in info.formats if f.get("filesize") or f.get("filesize_approx")]
        if not sizes:
            return "Inconnue"
        size_mb = max(sizes) / (1024 * 1024)
        return f"{size_mb:.2f} MB"

    def _format_duration(self, seconds):
        if not seconds:
            return "??:??"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _select_video_format(self):
        videos = self.info.get_video_formats_mp4()
        if not videos:
            return None

        res = self.resolution_combo.get()

        if res == "Best":
            return max(videos, key=lambda f: f["height"])

        height = int(res[:-1])  # "1080p" → 1080
        eligible = [f for f in videos if f["height"] <= height]

        return max(eligible, key=lambda f: f["height"]) if eligible else None

    def _select_audio_format(self):
        audios = self.info.get_audio_formats_m4a()
        if not audios:
            return None

        br = self.bitrate_combo.get()

        if br == "Best":
            return max(audios, key=lambda f: f["abr"])

        target = int(br.replace(" kbps", ""))
        eligible = [f for f in audios if abs(f["abr"] - target) <= 10]

        return max(eligible, key=lambda f: f["abr"]) if eligible else None

    def compute_selected_size(self):
        total = 0

        if self.download_type.get() == "video":
            video = self._select_video_format()
            audio = self._select_audio_format()

            if video:
                total += video["filesize"]
            if audio:
                total += audio["filesize"]

        else:  # AUDIO ONLY
            audio = self._select_audio_format()
            if audio:
                total += audio["filesize"]  # MP3 = taille du M4A source

        return total

    def refresh_size_display(self):
        size = self.compute_selected_size()
        size_mb = size / (1024 * 1024)

        duration = self._format_duration(getattr(self.info, "duration", 0))
        self.extra_info_label.configure(
            text=f"⏱ {duration}   |   💾 {size_mb:.2f} MB"
        )

        # prévenir l’onglet parent
        if hasattr(self.parent_tab, "refresh_download_button"):
            self.parent_tab.refresh_download_button()

    def get_options(self):
        res = self.resolution_combo.get()
        br = self.bitrate_combo.get()

        return {
            "url": getattr(self.info, "url", None),
            "title": getattr(self.info, "title", None),
            "type": self.download_type.get(),
            "resolution": None if res == "Best" else res,
            "bitrate": None if br == "Best" else br,
            "audio_format": self.audio_format.get()
        }

        return {
            "url": getattr(self.info, "url", None),
            "title": getattr(self.info, "title", None),
            "type": self.download_type.get(),
            "resolution": None if res == "Best" else res,
            "bitrate": None if br == "Best" else br
        }

    def refresh_texts(self):
        """Met à jour les textes traduits pour cette vidéo."""
        self.radio_video.configure(text=get_text("video_option", self.app.current_language))
        self.radio_audio.configure(text=get_text("audio_only_option", self.app.current_language))
        self.resolution_label.configure(text=get_text("resolution_label", self.app.current_language))
        self.bitrate_label.configure(text=get_text("audio_bitrate_label", self.app.current_language))

    def show_info(self):
        """Affiche les infos détaillées dans une popup. Utilise get_detailed_summary() si disponible."""
        # Récupère texte via get_detailed_summary si présent, sinon on compose un fallback
        if hasattr(self.info, "get_detailed_summary"):
            info_text = self.info.get_detailed_summary()
        else:
            # fallback minimal
            info_text = (
                f"Titre: {getattr(self.info, 'title', '')}\n"
                f"Durée: {self._format_duration(getattr(self.info, 'duration', 0))}\n"
                f"Résolutions: {', '.join(getattr(self.info, 'resolutions', []) or [])}\n"
                f"Bitrates audio: {', '.join(str(int(b)) for b in (getattr(self.info, 'audio_bitrates', []) or []))}\n\n"
                f"Formats disponibles (extraits):\n"
            )
            for f in (getattr(self.info, "formats", []) or [])[:30]:
                info_text += f"- id:{f.get('format_id')} ext:{f.get('ext')} res:{f.get('resolution') or f.get('height')} abr:{f.get('abr')}\n"

        def show_video_table(parent, video_info):
            headers, rows = video_info.get_table_data()

            tree = ttk.Treeview(parent, columns=headers, show="headings", height=10)
            for col in headers:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor="center")  # ajuste largeur

            for row in rows:
                tree.insert("", "end", values=row)

            tree.pack(fill="both", expand=True, padx=10, pady=10)

        # popup
        popup = ctk.CTkToplevel(self)
        popup.title(
            get_text("video_info_title", self.app.current_language) if hasattr(get_text, "__call__") else "Infos vidéo")
        popup.geometry("700x450")

        tabview = ctk.CTkTabview(popup)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet texte
        tab_text = tabview.add("Résumé texte")
        textbox = ctk.CTkTextbox(tab_text, wrap="word", font=("Ubuntu Mono", 12))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("1.0", info_text)
        textbox.configure(state="disabled")

        # Onglet tableau
        tab_table = tabview.add("Tableau")
        show_video_table(tab_table, self.info)


class SingleDownloadTab:
    """L'onglet 'Téléchargement unique', gère une liste de vidéos à télécharger."""

    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.video_frames = []  # liste des VideoItemFrame
        self.active_threads = []  # threads en cours
        self._thread_progress = {}      # mapping thread -> percent (0..100)
        self.placeholder_label = None  # label par défaut
        self.is_downloading = False  # 🔑 nouvel état
        self._download_results = []  # liste de True / False
        self.build_ui()

    def build_ui(self):
        # Entrée URL + bouton "Vérifier"
        url_frame = ctk.CTkFrame(self.parent)
        url_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.url_input = ctk.CTkEntry(
            url_frame,
            width=400,
            placeholder_text=get_text("url_placeholder", self.app.current_language)
        )
        self.url_input.pack(side="left", padx=5, fill="x", expand=True)

        self.check_url_btn = ctk.CTkButton(
            url_frame,
            text="➕ " + get_text("check_button", self.app.current_language),
            command=self.check_url
        )
        self.check_url_btn.pack(side="left", padx=5)

        # Bouton : charger une liste d’URLs depuis un fichier
        self.load_file_btn = ctk.CTkButton(
            url_frame,
            text="⬆️ " + get_text("load_from_file_button", self.app.current_language),
            command=self.load_urls_from_file
        )
        self.load_file_btn.pack(side="left", padx=5)

        # Frame qui va contenir toutes les vidéos ajoutées
        self.playlist_frame = ctk.CTkScrollableFrame(self.parent, orientation="vertical", height=100)
        self.playlist_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Texte par défaut
        self.show_placeholder()

        # Bouton unique Download/Cancel (centré)
        buttons_frame = ctk.CTkFrame(self.parent)
        buttons_frame.pack(fill="x", pady=5)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=0)
        buttons_frame.grid_columnconfigure(2, weight=1)

        self.download_btn = ctk.CTkButton(
            buttons_frame,
            text="⬇️ " + get_text("download_button", self.app.current_language),
            command=self.start_download_all,
            state="disabled",
            width=400
        )
        self.download_btn.grid(row=0, column=1, pady=10)

        # Progression + statut
        self.single_status_label = ctk.CTkLabel(self.parent, text=get_text("ready_status", self.app.current_language))
        self.single_status_label.pack(fill="x", padx=10, pady=0)

        self.single_progress_bar = ctk.CTkProgressBar(self.parent)
        self.single_progress_bar.pack(fill="x", padx=10, pady=0)
        self.single_progress_bar.set(0)


    # ---------------- UI helpers ----------------

    def refresh_texts(self):
        """Met à jour les textes traduits de l'onglet 'Téléchargement unique'."""
        # Champ URL
        self.url_input.configure(placeholder_text=get_text("url_placeholder", self.app.current_language))
        self.check_url_btn.configure(text="✔️ " + get_text("check_button", self.app.current_language))
        self.load_file_btn.configure(text="⬆️ " + get_text("load_from_file_button", self.app.current_language))

        # texte du bouton selon l'état
        if self.is_downloading:
            self.download_btn.configure(text="↩️ " + get_text("cancel_button", self.app.current_language))
        else:
            self.download_btn.configure(text="⬇️ " + get_text("download_button", self.app.current_language))

        # statut / placeholder
        if not self.is_downloading:
            self.single_status_label.configure(text=get_text("ready_status", self.app.current_language))

        if self.placeholder_label is not None:
            self.placeholder_label.configure(text=get_text("no_file_in_the_queue", self.app.current_language))

        # Mettre aussi à jour les textes dans chaque frame de vidéo déjà ajoutée
        for vf in self.video_frames:
            if hasattr(vf, "refresh_texts"):
                vf.refresh_texts()

        # Bouton télécharger
        self.refresh_download_button()

    def show_placeholder(self):
        """Affiche le texte 'Aucun fichier' si la file est vide."""
        if not self.video_frames and self.placeholder_label is None:
            self.placeholder_label = ctk.CTkLabel(
                self.playlist_frame,
                text=get_text("no_file_in_the_queue", self.app.current_language),
                font=ctk.CTkFont(size=14, slant="italic")
            )
            self.placeholder_label.pack(pady=20)

    def hide_placeholder(self):
        """Supprime le placeholder si présent."""
        if self.placeholder_label is not None:
            self.placeholder_label.destroy()
            self.placeholder_label = None

    # ---------------- URL check / ajout ----------------

    def check_url(self):
        """Vérifie une URL saisie et ajoute une vidéo à la liste."""
        url = self.url_input.get().strip()
        if not url:
            messagebox.showwarning(get_text("warning", self.app.current_language), get_text("enter_valid_url", self.app.current_language))
            return
        self.check_url_btn.configure(state="disabled")

        # On crée une frame temporaire
        loading_frame = LoadingItemFrame(self.playlist_frame, self.app)
        loading_frame.pack(fill="x", pady=5)

        thread = InfoThread(
            url,
            self.app,
            callback=lambda info: self.app.after(0, lambda: self.on_info_received(info, loading_frame)),
            error_callback=lambda err: self.app.after(0, lambda: self.on_info_error(err, loading_frame))
        )
        thread.daemon = True
        thread.start()

    def load_urls_from_file(self):
        """Charge un fichier contenant des liens et ajoute chaque vidéo automatiquement."""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title=get_text("load_urls_list", self.app.current_language),
            filetypes=[(get_text("text_files", self.app.current_language), "*.txt")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            messagebox.showerror(get_text("error", self.app.current_language), f"Impossible de lire le fichier : {e}")
            return

        if not urls:
            messagebox.showwarning(get_text("warning", self.app.current_language), get_text("no_valid_urls", self.app.current_language))
            return

        # désactive bouton pendant le chargement multiple
        #self.check_url_btn.configure(state="disabled")
        #if hasattr(self, "load_file_btn"):
        #    self.load_file_btn.configure(state="disabled")

        # Lance la récupération d'infos pour chaque URL
        for url in urls:
            loading_frame = LoadingItemFrame(self.playlist_frame, self.app)
            loading_frame.pack(fill="x", pady=5)

            thread = InfoThread(
                url,
                self.app,
                callback=lambda info, lf=loading_frame: self.app.after(
                    0, lambda: self.on_info_received(info, lf)
                ),
                error_callback=lambda err, lf=loading_frame: self.app.after(
                    0, lambda: self.on_info_error(err, lf)
                )
            )
            thread.daemon = True
            thread.start()

        # Après lancement
        self.single_status_label.configure(
            text=get_text("loaded_urls", self.app.current_language, count=len(urls))
        )

    def on_info_received(self, info, loading_frame):
        loading_frame.stop()
        self.hide_placeholder()

        video_frame = VideoItemFrame(self.playlist_frame, self.app, info, self)
        video_frame.pack(fill="x", pady=5)
        self.video_frames.append(video_frame)

        self.url_input.delete(0, "end")
        self.check_url_btn.configure(state="normal")

        self.refresh_download_button()

        # si au moins un fichier -> activer le bouton (si pas en téléchargement)
        if not self.is_downloading:
            self.download_btn.configure(state="normal")

    def remove_video(self, video_frame):
        if video_frame in self.video_frames:
            video_frame.destroy()
            self.video_frames.remove(video_frame)

        if not self.video_frames:
            self.show_placeholder()
            # si plus de vidéos, désactiver bouton téléchargement si idle
            if not self.is_downloading:
                self.download_btn.configure(state="disabled")

        self.refresh_download_button()

    def on_info_error(self, error, loading_frame):
        loading_frame.stop()
        self.check_url_btn.configure(state="normal")
        messagebox.showerror(get_text("error", self.app.current_language), f"{get_text('error_prefix', self.app.current_language)} {error}")

    # ---------------- téléchargement (toggle bouton unique) ----------------

    def compute_total_size(self):
        return sum(vf.compute_selected_size() for vf in self.video_frames)

    def refresh_download_button(self):
        if not self.video_frames:
            self.download_btn.configure(
                text="⬇️ " + get_text("download_button", self.app.current_language),
                state="disabled"
            )
            return

        total = self.compute_total_size()
        mb = total / (1024 * 1024)

        self.download_btn.configure(
            text=f"⬇️ {get_text('download_button', self.app.current_language)} – {mb:.2f} MB",
            state="normal" if not self.is_downloading else "normal"
        )

    def start_download_all(self):
        self._download_results.clear()

        """Démarre tous les téléchargements et transforme le bouton en 'Annuler'."""
        if not self.video_frames:
            return

        # demander dossier de sortie
        output_path = ask_output_folder(self.app.current_language, self.app.output_path)
        if not output_path:
            return
        self.app.output_path = output_path

        self.active_threads.clear()
        self._thread_progress.clear()
        self.is_downloading = True

        # UI
        self.single_progress_bar.set(0)
        self.single_status_label.configure(text=get_text("download_started", self.app.current_language))
        self.download_btn.configure(text="↩️ " + get_text("cancel_button", self.app.current_language),
                                    command=self.cancel_downloads,
                                    state="normal"
                                    )

        self.check_url_btn.configure(state="disabled")

        # lancer un DownloadThread par vidéo, en collectant les callbacks correctement
        for vf in self.video_frames:
            opts = vf.get_options()

            # référence mutable pour binder le thread après création (astuce de closure)
            tref = {}

            def make_progress_cb(tref):
                def _progress(pct):
                    t = tref.get('t')
                    self.app.after(0, lambda: self._on_thread_progress(t, pct))
                return _progress

            def make_status_cb():
                return lambda txt: self.app.after(0, lambda: self.single_status_label.configure(text=txt))

            def make_finished_cb(tref):
                return lambda success: self.app.after(0, lambda: self._on_thread_finished(tref.get('t'), success))

            thread = DownloadThread(
                opts["url"],
                self.app,
                opts["type"],
                opts["resolution"],
                opts["bitrate"],
                opts["audio_format"],
                output_path,
                progress_callback=make_progress_cb(tref),
                status_callback=make_status_cb(),
                finished_callback=make_finished_cb(tref)
            )

            # bind le thread dans la référence et initialiser sa progression à 0
            tref['t'] = thread
            self._thread_progress[thread] = 0
            self.active_threads.append(thread)
            thread.daemon = True
            thread.start()

    def cancel_downloads(self):
        """Annule tous les téléchargements en cours et remet le bouton en mode 'Télécharger'."""
        for t in self.active_threads:
            try:
                t.cancel()
            except Exception:
                pass
        self.is_downloading = False
        self.download_btn.configure(text="⬇️ " + get_text("download_button", self.app.current_language),
                                    command=self.start_download_all,
                                    state="normal"
                                    )
        self.check_url_btn.configure(state="normal")
        self.single_status_label.configure(text=get_text("canceling_download", self.app.current_language) if get_text("canceling_download", self.app.current_language) else "Annulation en cours...")
        # facultatif : reset progress bar
        # self.single_progress_bar.set(0)

    # ----------- callbacks internes pour mise à jour UI -----------
    def _on_thread_progress(self, thread, pct):
        # stocke et calcule la moyenne
        self._thread_progress[thread] = pct
        if self._thread_progress:
            avg = sum(self._thread_progress.values()) / len(self._thread_progress)
        else:
            avg = 0
        self.single_progress_bar.set(avg / 100.0)

    def _on_thread_finished(self, thread, success):
        # mémorise le résultat
        self._download_results.append(success)
        self._thread_progress[thread] = 100

        # si tous les threads sont terminés
        if all(not t.is_alive() for t in self.active_threads):

            self.is_downloading = False

            # remettre le bouton en mode Télécharger
            self.download_btn.configure(
                text="⬇️ " + get_text("download_button", self.app.current_language),
                command=self.start_download_all,
                state="normal"
            )
            self.check_url_btn.configure(state="normal")
            self.single_progress_bar.set(1)

            # -------- POPUP UNIQUE --------
            if all(self._download_results):
                self.single_status_label.configure(
                    text=get_text("download_complete", self.app.current_language)
                )
                messagebox.showinfo(
                    get_text("download_complete", self.app.current_language),
                    get_text("download_complete_message", self.app.current_language)
                )
            else:
                self.single_status_label.configure(
                    text=get_text("download_failed", self.app.current_language)
                )
                messagebox.showwarning(
                    get_text("download_failed", self.app.current_language),
                    get_text("download_failed_message", self.app.current_language)
                )

            # reset pour le prochain batch
            self._download_results.clear()

class LoadingItemFrame(ctk.CTkFrame):
    """Frame temporaire affichée pendant le chargement des infos d'une vidéo."""
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.progress_bar = ctk.CTkProgressBar(self, mode="indeterminate", width=300)
        self.progress_bar.pack(pady=(10, 5))
        self.progress_bar.start()

        self.loading_text = ctk.CTkLabel(
            self,
            text=get_text("loading_video_info", self.app.current_language),
            font=ctk.CTkFont(size=13, slant="italic")
        )
        self.loading_text.pack()

    def refresh_texts(self):
        """Met à jour la traduction du texte de chargement."""
        self.loading_text.configure(text=get_text("loading_video_info", self.app.current_language))

    def stop(self):
        """Arrête et détruit la frame."""
        self.progress_bar.stop()
        self.destroy()
