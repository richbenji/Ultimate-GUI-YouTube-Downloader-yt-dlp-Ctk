import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .translations import get_text
from .download_threads import InfoThread, DownloadThread

class SingleDownloadTab:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.current_video_info = None
        self.download_thread = None
        self.build_ui()

    def build_ui(self):
        # URL
        url_frame = ctk.CTkFrame(self.parent)
        url_frame.pack(fill="x", padx=10, pady=(10, 5))
        self.url_label = ctk.CTkLabel(url_frame, text=get_text("youtube_url", self.app.current_language))
        self.url_label.pack(side="left", padx=5)
        self.url_input = ctk.CTkEntry(url_frame, width=400,
                                      placeholder_text=get_text("url_placeholder", self.app.current_language))
        self.url_input.pack(side="left", padx=5, fill="x", expand=True)
        self.check_url_btn = ctk.CTkButton(url_frame, text=get_text("check_button", self.app.current_language),
                                           command=self.check_url)
        self.check_url_btn.pack(side="left", padx=5)

        # Titre
        self.title_label = ctk.CTkLabel(self.parent, text=get_text("title_prefix", self.app.current_language))
        self.title_label.pack(fill="x", padx=10, pady=5)

        # Type (vidéo/audio)
        type_frame = ctk.CTkFrame(self.parent)
        type_frame.pack(fill="x", padx=10, pady=5)
        self.type_label = ctk.CTkLabel(type_frame, text=get_text("type_label", self.app.current_language))
        self.type_label.pack(side="left", padx=5)
        self.download_type_var = tk.StringVar(value="video")
        self.video_radio = ctk.CTkRadioButton(type_frame, text=get_text("video_option", self.app.current_language),
                                              variable=self.download_type_var, value="video",
                                              command=self.toggle_resolution_options)
        self.video_radio.pack(side="left", padx=10)
        self.audio_radio = ctk.CTkRadioButton(type_frame, text=get_text("audio_only_option", self.app.current_language),
                                              variable=self.download_type_var, value="audio",
                                              command=self.toggle_resolution_options)
        self.audio_radio.pack(side="left", padx=10)

        # Résolution
        res_frame = ctk.CTkFrame(self.parent)
        res_frame.pack(fill="x", padx=10, pady=5)
        self.resolution_label = ctk.CTkLabel(res_frame, text=get_text("resolution_label", self.app.current_language))
        self.resolution_label.pack(side="left", padx=5)
        self.resolution_var = tk.StringVar(value=get_text("choose_resolution", self.app.current_language))
        self.resolution_combo = ctk.CTkComboBox(res_frame, variable=self.resolution_var,
                                                values=[get_text("choose_resolution", self.app.current_language)])
        self.resolution_combo.pack(side="left", padx=5)

        # Bitrate
        bitrate_frame = ctk.CTkFrame(self.parent)
        bitrate_frame.pack(fill="x", padx=10, pady=5)
        self.bitrate_label = ctk.CTkLabel(bitrate_frame, text=get_text("audio_bitrate_label", self.app.current_language))
        self.bitrate_label.pack(side="left", padx=5)
        self.bitrate_var = tk.StringVar(value="Auto")
        self.bitrate_combo = ctk.CTkComboBox(bitrate_frame, variable=self.bitrate_var,
                                             values=["Auto", "320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"])
        self.bitrate_combo.pack(side="left", padx=5)

        # Dossier
        output_frame = ctk.CTkFrame(self.parent)
        output_frame.pack(fill="x", padx=10, pady=5)
        self.output_label = ctk.CTkLabel(output_frame, text=get_text("output_folder_label", self.app.current_language))
        self.output_label.pack(side="left", padx=5)
        self.output_path_var = tk.StringVar(value=self.app.output_path)
        self.output_path_entry = ctk.CTkEntry(output_frame, textvariable=self.output_path_var, width=350)
        self.output_path_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.browse_btn = ctk.CTkButton(output_frame, text=get_text("browse_button", self.app.current_language),
                                        command=self.select_output_folder)
        self.browse_btn.pack(side="left", padx=5)

        # Boutons
        buttons_frame = ctk.CTkFrame(self.parent)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        self.download_btn = ctk.CTkButton(buttons_frame, text=get_text("download_button", self.app.current_language),
                                          command=self.start_download, state="disabled")
        self.download_btn.pack(side="left", padx=5)
        self.cancel_btn = ctk.CTkButton(buttons_frame, text=get_text("cancel_button", self.app.current_language),
                                        command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side="left", padx=5)

        # Progression et statut
        self.progress_bar = ctk.CTkProgressBar(self.parent)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(self.parent, text=get_text("ready_status", self.app.current_language))
        self.status_label.pack(fill="x", padx=10, pady=5)

    def refresh_texts(self):
        self.url_label.configure(text=get_text("youtube_url", self.app.current_language))
        self.url_input.configure(placeholder_text=get_text("url_placeholder", self.app.current_language))
        self.check_url_btn.configure(text=get_text("check_button", self.app.current_language))
        self.type_label.configure(text=get_text("type_label", self.app.current_language))
        self.video_radio.configure(text=get_text("video_option", self.app.current_language))
        self.audio_radio.configure(text=get_text("audio_only_option", self.app.current_language))
        self.resolution_label.configure(text=get_text("resolution_label", self.app.current_language))
        self.bitrate_label.configure(text=get_text("audio_bitrate_label", self.app.current_language))
        self.output_label.configure(text=get_text("output_folder_label", self.app.current_language))
        self.browse_btn.configure(text=get_text("browse_button", self.app.current_language))
        self.download_btn.configure(text=get_text("download_button", self.app.current_language))
        self.cancel_btn.configure(text=get_text("cancel_button", self.app.current_language))
        self.resolution_var.set(get_text("choose_resolution", self.app.current_language))
        self.status_label.configure(text=get_text("ready_status", self.app.current_language))

    def check_url(self):
        url = self.url_input.get().strip()
        if not url:
            self.status_label.configure(text=get_text("enter_valid_url", self.app.current_language))
            return
        self.status_label.configure(text=get_text("checking_url", self.app.current_language))
        self.check_url_btn.configure(state="disabled")
        thread = InfoThread(
            url,
            callback=lambda info: self.app.after(0, lambda: self.on_info_received(info)),
            error_callback=lambda err: self.app.after(0, lambda: self.on_info_error(err))
        )
        thread.daemon = True
        thread.start()

    def on_info_received(self, info):
        self.current_video_info = info
        self.title_label.configure(text=f"{get_text('title_prefix', self.app.current_language)}{info.title}")
        self.resolution_combo.configure(values=info.resolutions or ["1080p", "720p", "480p", "360p", "240p"])
        self.resolution_combo.set(info.resolutions[0] if info.resolutions else "720p")
        bitrates = ["Auto"] + [f"{b} kbps" for b in info.audio_bitrates] or ["320 kbps", "256 kbps", "192 kbps"]
        self.bitrate_combo.configure(values=bitrates)
        self.bitrate_combo.set("Auto")
        self.status_label.configure(text=f"{get_text('video_found', self.app.current_language)}{info.title}")
        self.download_btn.configure(state="normal")
        self.check_url_btn.configure(state="normal")

    def on_info_error(self, error):
        self.status_label.configure(text=f"{get_text('error_prefix', self.app.current_language)}{error}")
        self.check_url_btn.configure(state="normal")
        self.download_btn.configure(state="disabled")

    def toggle_resolution_options(self):
        if self.download_type_var.get() == "video":
            self.resolution_combo.configure(state="normal")
        else:
            self.resolution_combo.configure(state="disabled")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title=get_text("select_output_folder", self.app.current_language))
        if folder:
            self.app.output_path = folder
            self.output_path_var.set(folder)

    def start_download(self):
        url = self.url_input.get().strip()
        if self.download_type_var.get() == "video" and not self.resolution_var.get():
            self.status_label.configure(text=get_text("select_resolution", self.app.current_language))
            return
        self.download_thread = DownloadThread(
            url,
            self.download_type_var.get(),
            self.resolution_var.get(),
            self.bitrate_var.get(),
            self.output_path_var.get(),
            lambda v: self.app.after(0, lambda: self.progress_bar.set(v/100)),
            lambda t: self.app.after(0, lambda: self.status_label.configure(text=t)),
            lambda s: self.app.after(0, lambda: self.download_finished(s))
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
            self.status_label.configure(text=get_text("canceling_download", self.app.current_language))
            self.cancel_btn.configure(state="disabled")

    def download_finished(self, success):
        self.download_btn.configure(state="normal")
        self.check_url_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        if success:
            self.progress_bar.set(1)
            messagebox.showinfo(get_text("download_complete", self.app.current_language),
                                get_text("download_complete_message", self.app.current_language))
