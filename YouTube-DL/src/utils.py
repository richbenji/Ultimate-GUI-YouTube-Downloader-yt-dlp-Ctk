import os
import customtkinter as ctk
from PIL import Image
from tkinter import filedialog
from .translations import get_text

def load_custom_font(font_path, fallback=("Arial", 28, "bold")):
    try:
        if os.path.exists(font_path):
            ctk.FontManager.load_font(font_path)
            return ctk.CTkFont(family="TradeGothic", size=28, weight="bold")
        else:
            return ctk.CTkFont(family=fallback[0], size=fallback[1], weight=fallback[2])
    except Exception as e:
        print(f"Erreur lors du chargement de la police: {e}")
        return ctk.CTkFont(family=fallback[0], size=fallback[1], weight=fallback[2])

def load_logo_image(logo_path, size=(80, 60)):
    try:
        if os.path.exists(logo_path):
            pil_image = Image.open(logo_path).resize(size, Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
    except Exception as e:
        print(f"Erreur lors du chargement du logo: {e}")
    return None

def ask_output_folder(language, last_folder=None):
    """
    Ouvre une boîte de dialogue pour choisir un dossier de sortie.
    Retourne le chemin choisi ou None si annulé.
    """
    initialdir = last_folder if last_folder else "/"
    folder = filedialog.askdirectory(
        title=get_text("select_output_folder", language),
        initialdir=initialdir
    )
    return folder

def format_bytes_iec(size_bytes, precision=2):
    """
    Convertit une taille en octets vers o / Kio / Mio / Gio / Tio (IEC).
    """
    if size_bytes is None:
        return "N/A"

    try:
        size_bytes = float(size_bytes)
    except (TypeError, ValueError):
        return "N/A"

    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    factor = 1024.0

    for unit in units:
        if size_bytes < factor:
            return f"{size_bytes:.{precision}f} {unit}"
        size_bytes /= factor

    return f"{size_bytes:.{precision}f} PiB"

