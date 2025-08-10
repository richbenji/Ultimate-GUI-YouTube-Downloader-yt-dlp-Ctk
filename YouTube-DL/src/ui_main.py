import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .translations import get_text
from .utils import load_custom_font, load_logo_image
from .ui_single_tab import SingleDownloadTab
from .ui_batch_tab import BatchDownloadTab

class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Langue par défaut
        self.current_language = "fr"

        # Langues disponibles
        self.available_languages = {
            "fr": "Français",
            "en": "English",
            "es": "Español",
            "it": "Italiano",
            "de": "Deutsch"
        }

        self.title(get_text("app_title", self.current_language))
        self.geometry("800x700")

        # Apparence
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Dossier de sortie par défaut
        self.download_folder = get_text("download_folder", self.current_language)
        self.output_path = os.path.join(os.path.expanduser("~"), self.download_folder)

        # Interface
        self.setup_header()
        self.setup_tabs()

    def setup_header(self):
        header_frame = ctk.CTkFrame(self, height=120)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)

        # Sélecteur de langue
        language_frame = ctk.CTkFrame(header_frame, width=140)
        language_frame.pack(side="left", padx=10, pady=10)
        language_frame.pack_propagate(False)
        language_label = ctk.CTkLabel(language_frame, text="🌐", font=ctk.CTkFont(size=16))
        language_label.pack(pady=(5, 0))
        self.language_combo = ctk.CTkComboBox(
            master=language_frame,
            values=list(self.available_languages.values()),
            command=self.change_language,
            width=120,
            height=28
        )
        self.language_combo.set(self.available_languages[self.current_language])
        self.language_combo.pack(pady=(0, 5))

        # Logo
        logo_image = load_logo_image("assets/Youtube_logo.png")
        if logo_image:
            logo_frame = ctk.CTkFrame(header_frame, width=100, height=100)
            logo_frame.pack(side="right", padx=10, pady=10)
            logo_frame.pack_propagate(False)
            logo_label = ctk.CTkLabel(logo_frame, image=logo_image, text="")
            logo_label.pack(expand=True)

        # Titre et sous-titre
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(expand=True, fill="both", padx=10, pady=10)
        title_font = load_custom_font("fonts/TradeGothic Bold.ttf")
        self.title_label_main = ctk.CTkLabel(
            title_frame,
            text=get_text("app_title", self.current_language),
            font=title_font,
            text_color=("#1f538d", "#14375e"),
            pady=5
        )
        self.title_label_main.pack(expand=True)
        self.subtitle_label_main = ctk.CTkLabel(
            title_frame,
            text=get_text("app_subtitle", self.current_language),
            font=ctk.CTkFont(family="Arial", size=14, slant="italic"),
            text_color=("#666666", "#999999")
        )
        self.subtitle_label_main.pack(expand=True)

    def setup_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglets
        self.tab_single = self.tabview.add(get_text("single_download_tab", self.current_language))
        self.tab_batch = self.tabview.add(get_text("batch_download_tab", self.current_language))

        # Injection des sous-interfaces
        self.single_tab_ui = SingleDownloadTab(self.tab_single, self)
        self.batch_tab_ui = BatchDownloadTab(self.tab_batch, self)

    def change_language(self, selected_language_name):
        for lang_code, lang_name in self.available_languages.items():
            if lang_name == selected_language_name:
                self.current_language = lang_code
                self.refresh_ui()
                break

    def refresh_ui(self):
        self.title(get_text("app_title", self.current_language))
        self.title_label_main.configure(text=get_text("app_title", self.current_language))
        self.subtitle_label_main.configure(text=get_text("app_subtitle", self.current_language))
        self.language_combo.set(self.available_languages[self.current_language])
        self.single_tab_ui.refresh_texts()
        self.batch_tab_ui.refresh_texts()
