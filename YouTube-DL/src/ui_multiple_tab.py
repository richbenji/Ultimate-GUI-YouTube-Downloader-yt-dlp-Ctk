import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from .translations import get_text

class MultipleDownloadTab:
    def __init__(self, parent, app):
        self.app = app
        self.parent = parent
        self.current_video_info = None
        self.multiple_download_thread = None
        self.build_ui()

    def build_ui(self):
        # URL
        url_frame = ctk.CTkFrame(self.parent)
        url_frame.pack(fill="x", padx=10, pady=(10, 5))
