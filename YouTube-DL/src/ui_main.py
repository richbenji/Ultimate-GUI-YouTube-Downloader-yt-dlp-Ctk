import os
import customtkinter as ctk
from .translations import get_text
from .utils import load_custom_font, load_logo_image
from .ui_single_tab import SingleDownloadTab
from .ui_batch_tab import BatchDownloadTab
from .ui_multiple_tab import MultipleDownloadTab


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
        self.appearance_mode = "System"  # suivi du mode choisi
        ctk.set_appearance_mode("System")  # au démarrage, suivre le système
        ctk.set_default_color_theme("blue")

        # Dossier de sortie par défaut
        self.download_folder = get_text("download_folder", self.current_language)
        self.output_path = os.path.join(os.path.expanduser("~"), self.download_folder)

        # Interface
        self.setup_header()
        self.setup_tabs()

    def setup_header(self):
        header_frame = ctk.CTkFrame(self, height=100)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        header_frame.grid_propagate(False)

        # Centrage vertical et horizontal
        header_frame.grid_rowconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=1)

        # === Colonne gauche : switch + langue ===
        left_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="nsw", padx=10, pady=10)
        left_container.grid_rowconfigure((0, 1), weight=1)  # pour centrer verticalement

        # Switch Dark/Light (ligne 0)
        self.theme_switch = ctk.CTkSwitch(
            left_container,
            text="🌙 / ☀️",
            command=self.toggle_theme
        )
        self.theme_switch.grid(row=0, column=0, sticky="w", pady=(0, 5))
        if self.appearance_mode == "Dark":
            self.theme_switch.select()
        elif self.appearance_mode == "Light":
            self.theme_switch.deselect()

        # Langue (ligne 1)
        lang_frame = ctk.CTkFrame(left_container, fg_color="transparent")
        lang_frame.grid(row=1, column=0, sticky="w")

        self.language_combo = ctk.CTkComboBox(
            master=lang_frame,
            values=list(self.available_languages.values()),
            command=self.change_language,
            width=120,
            height=28
        )
        self.language_combo.set(self.available_languages[self.current_language])
        self.language_combo.pack(side="left")

        language_label = ctk.CTkLabel(lang_frame, text="🌐", font=ctk.CTkFont(size=16))
        language_label.pack(side="right", padx=(10,0))

        # === Colonne centrale : titre + sous-titre ===
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        title_font = load_custom_font("fonts/TradeGothic Bold.ttf")
        self.title_label_main = ctk.CTkLabel(
            title_container,
            text=get_text("app_title", self.current_language),
            font=title_font,
            text_color=("#1f538d", "#3B8ED0"),
            pady=5
        )
        self.title_label_main.pack(expand=True)
        self.subtitle_label_main = ctk.CTkLabel(
            title_container,
            text=get_text("app_subtitle", self.current_language),
            font=ctk.CTkFont(family="Arial", size=14, slant="italic"),
            text_color=("#666666", "#999999")
        )
        self.subtitle_label_main.pack(expand=True)

        # === Colonne droite : logo ===
        logo_image = load_logo_image("assets/Youtube_logo.png")
        if logo_image:
            logo_label = ctk.CTkLabel(header_frame, image=logo_image, text="")
            logo_label.grid(row=0, column=2, sticky="nse", padx=10, pady=10)

    def setup_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglets
        self.tab_single = self.tabview.add(get_text("single_download_tab", self.current_language))
        self.tab_batch = self.tabview.add(get_text("batch_download_tab", self.current_language))
        self.tab_multiple = self.tabview.add(get_text("multiple_download_tab", self.current_language))

        # Injection des sous-interfaces
        self.single_tab_ui = SingleDownloadTab(self.tab_single, self)
        self.batch_tab_ui = BatchDownloadTab(self.tab_batch, self)
        self.batch_tab_multiple = MultipleDownloadTab(self.tab_batch, self)

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.appearance_mode = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            self.appearance_mode = "Light"

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
