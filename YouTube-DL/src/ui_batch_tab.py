import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .translations import get_text
from .download_threads import BatchDownloadThread
from .utils import ask_output_folder


class BatchDownloadTab:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.batch_download_thread = None
        self.is_downloading = False  # 🔑 état courant
        self.build_ui()

    def build_ui(self):
        # Chargement depuis fichier
        file_frame = ctk.CTkFrame(self.parent)
        file_frame.pack(fill="x", padx=10, pady=10)
        self.load_file_btn = ctk.CTkButton(
            file_frame,
            text="⬆️ " + get_text("load_from_file_button", self.app.current_language),
            command=self.load_urls_from_file
        )
        self.load_file_btn.pack(side="left", padx=5)

        # Zone de texte pour URLs
        urls_frame = ctk.CTkFrame(self.parent)
        urls_frame.pack(fill="x", padx=10, pady=(0, 0))
        self.urls_label = ctk.CTkLabel(urls_frame, text=get_text("urls_list_label", self.app.current_language))
        self.urls_label.pack(anchor="w", padx=5, pady=0)
        self.urls_text = ctk.CTkTextbox(urls_frame, height=150)
        self.urls_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Type (vidéo/audio)
        type_frame = ctk.CTkFrame(self.parent)
        type_frame.pack(fill="x", padx=10, pady=5)
        self.batch_type_label = ctk.CTkLabel(type_frame, text=get_text("type_label", self.app.current_language))
        self.batch_type_label.pack(side="left", padx=5)
        self.batch_download_type_var = tk.StringVar(value="video")
        self.batch_video_radio = ctk.CTkRadioButton(type_frame, text=get_text("video_option", self.app.current_language),
                                                    variable=self.batch_download_type_var, value="video",
                                                    command=self.toggle_resolution_options)
        self.batch_video_radio.pack(side="left", padx=10)
        self.batch_audio_radio = ctk.CTkRadioButton(type_frame, text=get_text("audio_only_option", self.app.current_language),
                                                    variable=self.batch_download_type_var, value="audio",
                                                    command=self.toggle_resolution_options)
        self.batch_audio_radio.pack(side="left", padx=10)

        # Résolution
        res_frame = ctk.CTkFrame(self.parent)
        res_frame.pack(fill="x", padx=10, pady=5)
        self.batch_resolution_label = ctk.CTkLabel(res_frame,
                                                   text=get_text("resolution_label", self.app.current_language)
                                                   )
        self.batch_resolution_label.pack(side="left", padx=5)
        self.batch_resolution_var = tk.StringVar(value="720p")
        self.batch_resolution_combo = ctk.CTkComboBox(
            res_frame,
            variable=self.batch_resolution_var,
            values=["1080p", "720p", "480p", "360p", "240p", "144p"]
        )
        self.batch_resolution_combo.pack(side="left", padx=5)

        # Bitrate
        bitrate_frame = ctk.CTkFrame(self.parent)
        bitrate_frame.pack(fill="x", padx=10, pady=5)
        self.batch_bitrate_label = ctk.CTkLabel(bitrate_frame,
                                                text=get_text("audio_bitrate_label", self.app.current_language)
                                                )
        self.batch_bitrate_label.pack(side="left", padx=5)
        self.batch_bitrate_var = tk.StringVar(value="Best")
        self.batch_bitrate_combo = ctk.CTkComboBox(
            bitrate_frame,
            variable=self.batch_bitrate_var,
            values=["Best", "320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"]
        )
        self.batch_bitrate_combo.pack(side="left", padx=5)

        # Bouton unique Download/Cancel
        buttons_frame = ctk.CTkFrame(self.parent)
        buttons_frame.pack(fill="x", pady=5)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=0)
        buttons_frame.grid_columnconfigure(2, weight=1)

        self.batch_download_btn = ctk.CTkButton(
            buttons_frame,
            text="⬇️ " + get_text("download_button", self.app.current_language),
            command=self.start_batch_download,
            width=400
        )
        self.batch_download_btn.grid(row=0, column=1, pady=10)

        # Progression et statut
        self.batch_status_label = ctk.CTkLabel(self.parent, text=get_text("ready_status", self.app.current_language))
        self.batch_status_label.pack(fill="x", padx=10, pady=0)
        self.batch_progress_bar = ctk.CTkProgressBar(self.parent)
        self.batch_progress_bar.pack(fill="x", padx=10, pady=0)
        self.batch_progress_bar.set(0)


    # ---------------- Helpers ----------------

    def refresh_texts(self):
        self.urls_label.configure(text=get_text("urls_list_label", self.app.current_language))
        self.batch_type_label.configure(text=get_text("type_label", self.app.current_language))
        self.batch_video_radio.configure(text=get_text("video_option", self.app.current_language))
        self.batch_audio_radio.configure(text=get_text("audio_only_option", self.app.current_language))
        self.batch_resolution_label.configure(text=get_text("resolution_label", self.app.current_language))
        self.batch_bitrate_label.configure(text=get_text("audio_bitrate_label", self.app.current_language))
        self.load_file_btn.configure(text="⬆️ " + get_text("load_from_file_button", self.app.current_language))

        # texte bouton selon état
        if self.is_downloading:
            self.batch_download_btn.configure(text="↩️ " + get_text("cancel_button", self.app.current_language))
        else:
            self.batch_download_btn.configure(text="⬇️ " + get_text("download_button", self.app.current_language))

        if not self.is_downloading:
            self.batch_status_label.configure(text=get_text("ready_status", self.app.current_language))

    def toggle_resolution_options(self):
        if self.batch_download_type_var.get() == "video":
            self.batch_resolution_combo.configure(state="normal")
        else:
            self.batch_resolution_combo.configure(state="disabled")

    def load_urls_from_file(self):
        file_path = filedialog.askopenfilename(
            title=get_text("load_urls_list", self.app.current_language),
            filetypes=[(get_text("text_files", self.app.current_language), "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = f.readlines()
                self.urls_text.delete("0.0", "end")
                self.urls_text.insert("0.0", ''.join(urls))
                self.batch_status_label.configure(
                    text=get_text("loaded_urls", self.app.current_language, count=len(urls)))
            except Exception as e:
                self.batch_status_label.configure(
                    text=get_text("file_load_error", self.app.current_language, error=str(e)))

    # ---------------- Téléchargement ----------------

    def start_batch_download(self):
        if self.is_downloading:
            # si déjà en cours → annulation
            return self.cancel_batch_download()

        urls_text = self.urls_text.get("0.0", "end").strip()
        urls = [u.strip() for u in urls_text.split("\n") if u.strip()]
        if not urls:
            self.batch_status_label.configure(text=get_text("no_valid_urls", self.app.current_language))
            return

        # dossier de sortie
        output_path = ask_output_folder(self.app.current_language, self.app.output_path)
        if not output_path:
            return
        self.app.output_path = output_path

        # reset état
        self.batch_progress_bar.set(0)
        self.batch_status_label.configure(text=get_text("download_started", self.app.current_language))
        self.is_downloading = True

        # bouton devient Annuler
        self.batch_download_btn.configure(
            text="↩️ " + get_text("cancel_button", self.app.current_language),
            command=self.cancel_batch_download,
            state="normal"
        )
        self.load_file_btn.configure(state="disabled")

        # lancer thread
        self.batch_download_thread = BatchDownloadThread(
            urls,
            self.app,
            self.batch_download_type_var.get(),
            self.batch_resolution_var.get(),
            self.batch_bitrate_var.get(),
            output_path,
            lambda v: self.app.after(0, lambda: self.batch_progress_bar.set(v / 100)),
            lambda t: self.app.after(0, lambda: self.batch_status_label.configure(text=t)),
            lambda s: self.app.after(0, lambda: self.download_finished(s))
        )
        self.batch_download_thread.daemon = True
        self.batch_download_thread.start()

    def cancel_batch_download(self):
        if self.batch_download_thread:
            self.batch_download_thread.cancel()
        self.is_downloading = False
        self.batch_download_btn.configure(
            text="⬇️ " + get_text("download_button", self.app.current_language),
            command=self.start_batch_download,
            state="normal"
        )
        self.load_file_btn.configure(state="normal")
        self.batch_status_label.configure(text=get_text("canceling_batch_download", self.app.current_language))

    def download_finished(self, success):
        self.is_downloading = False
        self.batch_download_btn.configure(
            text="⬇️ " + get_text("download_button", self.app.current_language),
            command=self.start_batch_download,
            state="normal"
        )
        self.load_file_btn.configure(state="normal")

        if success:
            self.batch_progress_bar.set(1)
            self.batch_status_label.configure(text=get_text("batch_download_complete", self.app.current_language))
            try:
                messagebox.showinfo(get_text("batch_download_complete", self.app.current_language),
                                    get_text("batch_download_complete_message", self.app.current_language))
            except Exception:
                pass
        else:
            self.batch_status_label.configure(text=get_text("download_failed", self.app.current_language))