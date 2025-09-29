import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from .translations import get_text
from .download_threads import InfoThread, DownloadThread

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
        super().__init__(parent)
        self.app = app
        self.info = info
        self.parent_tab = parent_tab  # référence vers SingleDownloadTab

        # variables
        self.download_type = tk.StringVar(value="video")
        self.resolution = tk.StringVar(value=info.resolutions[0] if info.resolutions else "720p")
        self.bitrate = tk.StringVar(value="Auto")

        # layout principal : 2 colonnes (0 = miniature, 1 = contenu)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        # on garde une seule ligne principale, la miniature occupera plusieurs "rows" visuellement
        # (la grille ci-dessous pour right_frame gérera la verticalité interne)

        # --- Colonne gauche : miniature (placeholder d'abord) ---
        self.thumb_label = ctk.CTkLabel(self, text="")
        # rowspan=3 pour que la miniature s'étende visuellement sur la hauteur des 3 sections du right_frame
        self.thumb_label.grid(row=0, column=0, rowspan=3, sticky="nw", padx=0, pady=0)
        if getattr(info, "thumbnail", None):
            self._load_thumbnail_async(info.thumbnail)

            # --- Colonne droite : right_frame (strictement en grid) ---
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=0)

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
        ctk.CTkRadioButton(
            type_frame,
            text=get_text("video_option", app.current_language),
            variable=self.download_type,
            value="video"
        ).pack(side="left", padx=6)
        ctk.CTkRadioButton(
            type_frame,
            text=get_text("audio_only_option", app.current_language),
            variable=self.download_type,
            value="audio"
        ).pack(side="left", padx=6)

        # Résolution
        res_frame = ctk.CTkFrame(opts_container, fg_color="transparent")
        res_frame.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(res_frame, text=get_text("resolution_label", app.current_language)).pack(side="left", padx=6)
        values_res = getattr(info, "resolutions", None) or ["1080p", "720p", "480p", "360p"]
        self.resolution_combo = ctk.CTkComboBox(res_frame, variable=self.resolution, values=values_res)
        self.resolution_combo.set(self.resolution.get())
        self.resolution_combo.pack(side="left", padx=6)

        # Bitrate
        br_frame = ctk.CTkFrame(opts_container, fg_color="transparent")
        br_frame.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(br_frame, text=get_text("audio_bitrate_label", app.current_language)).pack(side="left", padx=6)
        bitrates = getattr(info, "audio_bitrates", [])
        bitrate_values = ["Auto"] + [f"{int(b)} kbps" for b in bitrates]
        self.bitrate_combo = ctk.CTkComboBox(br_frame, variable=self.bitrate, values=bitrate_values)
        # default = Auto
        self.bitrate_combo.set(self.bitrate.get() or "Auto")
        self.bitrate_combo.pack(side="left", padx=6)

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

    # ------------------ Méthodes utilitaires ------------------ #
    def _load_thumbnail_async(self, url):
        """Télécharge la miniature en arrière-plan puis l'affiche."""
        if requests is None or Image is None:
            return

        def worker():
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content)).convert("RGB")
                    img.thumbnail((320, 180), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    self.app.after(0, lambda: self._set_thumbnail(ctk_img))
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

    def get_options(self):
        return {
            "url": getattr(self.info, "url", None),
            "title": getattr(self.info, "title", None),
            "type": self.download_type.get(),
            "resolution": self.resolution_combo.get(),
            "bitrate": self.bitrate_combo.get()
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

        # popup
        popup = ctk.CTkToplevel(self)
        popup.title(
            get_text("video_info_title", self.app.current_language) if hasattr(get_text, "__call__") else "Infos vidéo")
        popup.geometry("700x450")

        try:
            textbox = ctk.CTkTextbox(popup, wrap="word")
            textbox.pack(fill="both", expand=True, padx=10, pady=10)
            textbox.insert("1.0", info_text)
            textbox.configure(state="disabled")
        except Exception:
            # fallback si CTkTextbox indisponible
            txt = tk.Text(popup, wrap="word")
            txt.pack(fill="both", expand=True, padx=10, pady=10)
            txt.insert("1.0", info_text)
            txt.configure(state="disabled")


class SingleDownloadTab:
    """L'onglet 'Téléchargement unique', gère une liste de vidéos à télécharger."""

    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.video_frames = []  # liste des VideoItemFrame
        self.active_threads = []  # threads en cours
        self.placeholder_label = None  # label par défaut
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

        # Frame qui va contenir toutes les vidéos ajoutées
        self.playlist_frame = ctk.CTkScrollableFrame(self.parent, orientation="vertical", height=100)
        self.playlist_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Texte par défaut
        self.show_placeholder()

        # Sélecteur de dossier
        output_frame = ctk.CTkFrame(self.parent)
        output_frame.pack(fill="x", padx=10, pady=(5, 5))
        ctk.CTkLabel(output_frame, text="📁 " + get_text("output_folder_label", self.app.current_language)).pack(side="left",
                                                                                                         padx=5)
        self.output_path_var = tk.StringVar(value=self.app.output_path)
        self.output_path_entry = ctk.CTkEntry(output_frame, textvariable=self.output_path_var, width=350)
        self.output_path_entry.pack(side="left", padx=5, fill="x", expand=True)
        browse_btn = ctk.CTkButton(output_frame, text="🗃 " + get_text("browse_button", self.app.current_language),
                                   command=self.select_output_folder)
        browse_btn.pack(side="left", padx=5)

        # Boutons Download + Cancel
        buttons_frame = ctk.CTkFrame(self.parent)
        buttons_frame.pack(fill="x", pady=5)
        self.download_btn = ctk.CTkButton(
            buttons_frame,
            text="⬇️ " + get_text("download_button", self.app.current_language),
            command=self.start_download_all,
            state="disabled"
        )
        self.download_btn.pack(side="left", padx=5)
        self.cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="↩️ " + get_text("cancel_button", self.app.current_language),
            command=self.cancel_downloads,
            state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=5)

    def select_output_folder(self):
        """Choisir un dossier de sortie."""
        folder = ctk.filedialog.askdirectory(title=get_text("select_output_folder", self.app.current_language))
        if folder:
            self.app.output_path = folder
            self.output_path_var.set(folder)

    def refresh_texts(self):
        """Met à jour les textes traduits de l'onglet 'Téléchargement unique'."""
        # Champ URL
        self.url_input.configure(placeholder_text=get_text("url_placeholder", self.app.current_language))
        self.check_url_btn.configure(text="✔️ " + get_text("check_button", self.app.current_language))

        # Labels et boutons du dossier de sortie
        for child in self.output_path_entry.master.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(text="📁 " + get_text("output_folder_label", self.app.current_language))
            elif isinstance(child, ctk.CTkButton) and child.cget("text") != get_text("download_button",
                                                                                     self.app.current_language):
                child.configure(text="🗃 " + get_text("browse_button", self.app.current_language))

        # Boutons Télécharger et Annuler
        self.download_btn.configure(text="⬇️ " + get_text("download_button", self.app.current_language))
        self.cancel_btn.configure(text="↩️ " + get_text("cancel_button", self.app.current_language))

        # Texte par défaut (si aucun fichier dans la queue)
        if self.placeholder_label is not None:
            self.placeholder_label.configure(text=get_text("no_files_placeholder", self.app.current_language))

        # Placeholder (aucune vidéo dans la file d’attente)
        if hasattr(self, "placeholder_label") and self.placeholder_label is not None:
            self.placeholder_label.configure(
                text=get_text("no_file_in_the_queue", self.app.current_language)
            )

        # Mettre aussi à jour les textes dans chaque vidéo déjà ajoutée
        for vf in self.video_frames:
            if hasattr(vf, "refresh_texts"):
                vf.refresh_texts()

    def check_url(self):
        """Vérifie une URL saisie et ajoute une vidéo à la liste."""
        url = self.url_input.get().strip()
        if not url:
            messagebox.showwarning("Attention", get_text("enter_valid_url", self.app.current_language))
            return
        self.check_url_btn.configure(state="disabled")

        # On crée une frame temporaire
        loading_frame = LoadingItemFrame(self.playlist_frame, self.app)
        loading_frame.pack(fill="x", pady=5)

        thread = InfoThread(
            url,
            callback=lambda info: self.app.after(0, lambda: self.on_info_received(info, loading_frame)),
            error_callback=lambda err: self.app.after(0, lambda: self.on_info_error(err, loading_frame))
        )
        thread.daemon = True
        thread.start()

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

    def on_info_received(self, info, loading_frame):
        """Quand les infos de la vidéo sont récupérées, remplacer le loading_frame par la vraie frame."""
        loading_frame.stop()  # supprime la frame de chargement
        self.hide_placeholder()

        """Quand les infos de la vidéo sont récupérées, créer une nouvelle carte."""
        video_frame = VideoItemFrame(self.playlist_frame, self.app, info, self)
        video_frame.pack(fill="x", pady=5)
        self.video_frames.append(video_frame)

        self.url_input.delete(0, "end")
        self.download_btn.configure(state="normal")
        self.check_url_btn.configure(state="normal")

    def remove_video(self, video_frame):
        """Retire une vidéo de la file et vérifie si on doit remettre le placeholder."""
        if video_frame in self.video_frames:
            video_frame.destroy()
            self.video_frames.remove(video_frame)

        if not self.video_frames:
            self.show_placeholder()

    def on_info_error(self, error, loading_frame):
        loading_frame.stop()  # supprime la frame de chargement
        self.check_url_btn.configure(state="normal")
        messagebox.showerror("Erreur", f"{get_text('error_prefix', self.app.current_language)} {error}")

    def start_download_all(self):
        """Lance le téléchargement de toutes les vidéos listées."""
        if not self.video_frames:
            return
        self.active_threads.clear()
        output_path = self.output_path_var.get()

        for vf in self.video_frames:
            opts = vf.get_options()
            thread = DownloadThread(
                opts["url"],
                opts["type"],
                opts["resolution"],
                opts["bitrate"],
                output_path,
                progress_callback=None,
                status_callback=None,
                finished_callback=lambda s: self.on_download_finished(s)
            )
            self.active_threads.append(thread)
            thread.daemon = True
            thread.start()

        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        messagebox.showinfo("Téléchargement", get_text("download_started", self.app.current_language))

    def cancel_downloads(self):
        """Annule tous les téléchargements en cours."""
        for t in self.active_threads:
            t.cancel()
        self.cancel_btn.configure(state="disabled")

    def on_download_finished(self, success):
        """Quand un téléchargement se termine (callback par thread)."""
        if all(not t.is_alive() for t in self.active_threads):
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")

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
