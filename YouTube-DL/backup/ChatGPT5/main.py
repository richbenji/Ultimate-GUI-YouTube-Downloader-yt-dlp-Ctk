# main.py
import threading
import queue
import os
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from languages import LANGUAGES
from downloader import get_formats, download_one

# -- UI constants --
ctk.set_appearance_mode("System")  # "Dark", "Light", "System"
ctk.set_default_color_theme("blue")

class YTDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.lang_code = "fr"
        self.trans = LANGUAGES[self.lang_code]
        self.title(self.trans["title"])
        self.geometry("720x520")
        self.minsize(600, 420)

        # queues pour communiquer entre threads et UI
        self.status_queue = queue.Queue()
        self.format_queue = queue.Queue()

        self.output_dir = os.getcwd()

        self.create_widgets()
        self.poll_queues()

    def create_widgets(self):
        # Top frame: language + folder
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=12, pady=(12, 6))

        # Language menu
        self.lang_option = ctk.CTkOptionMenu(top_frame, values=["Français", "English"], command=self.change_language)
        self.lang_option.set("Français" if self.lang_code == "fr" else "English")
        self.lang_option.pack(side="left", padx=(0,10))

        # Output folder
        self.folder_button = ctk.CTkButton(top_frame, text=self.trans["choose_folder"], command=self.choose_folder)
        self.folder_button.pack(side="right")
        self.folder_label = ctk.CTkLabel(top_frame, text=self.output_dir)
        self.folder_label.pack(side="right", padx=(0,10))

        # Links label + text
        self.links_label = ctk.CTkLabel(self, text=self.trans["enter_links"])
        self.links_label.pack(anchor="w", padx=12)
        self.links_box = ctk.CTkTextbox(self, height=120)
        self.links_box.pack(fill="x", padx=12, pady=(6,10))

        # Mid frame: controls
        mid_frame = ctk.CTkFrame(self)
        mid_frame.pack(fill="x", padx=12, pady=6)

        # Load formats button
        self.load_formats_btn = ctk.CTkButton(mid_frame, text=self.trans["load_formats"], command=self.load_formats_for_first_link)
        self.load_formats_btn.grid(row=0, column=0, padx=6, pady=6, sticky="w")

        # Download type
        self.type_label = ctk.CTkLabel(mid_frame, text=self.trans["download_type"])
        self.type_label.grid(row=0, column=1, padx=(12,2))
        self.type_option = ctk.CTkOptionMenu(mid_frame, values=[self.trans["video"], self.trans["audio"]], command=self.on_type_change)
        self.type_option.set(self.trans["video"])
        self.type_option.grid(row=0, column=2, padx=6)

        # Resolution selector
        self.res_label = ctk.CTkLabel(mid_frame, text=self.trans["resolution"])
        self.res_label.grid(row=1, column=0, padx=(0,6), pady=(6,0), sticky="w")
        self.res_option = ctk.CTkOptionMenu(mid_frame, values=["Aucune (charger d'abord)"])
        self.res_option.set("Aucune (charger d'abord)")
        self.res_option.grid(row=1, column=1, columnspan=2, padx=6, pady=(6,0), sticky="we")

        # Start button
        self.download_button = ctk.CTkButton(self, text=self.trans["start_download"], command=self.start_download_thread)
        self.download_button.pack(pady=12)

        # Status area
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="both", expand=True, padx=12, pady=(0,12))

        self.status_label = ctk.CTkLabel(bottom_frame, text=f"{self.trans['status']} ")
        self.status_label.pack(anchor="w", padx=6, pady=(6,0))

        self.status_box = ctk.CTkTextbox(bottom_frame, height=140, state="normal")
        self.status_box.pack(fill="both", expand=True, padx=6, pady=6)

    def change_language(self, choice):
        self.lang_code = "fr" if choice == "Français" else "en"
        self.trans = LANGUAGES[self.lang_code]
        self.update_texts()

    def update_texts(self):
        self.title(self.trans["title"])
        self.links_label.configure(text=self.trans["enter_links"])
        self.load_formats_btn.configure(text=self.trans["load_formats"])
        self.type_label.configure(text=self.trans["download_type"])
        self.type_option.configure(values=[self.trans["video"], self.trans["audio"]])
        # Keep the set value but if it was video/audio, map accordingly
        current = self.type_option.get()
        if current in (LANGUAGES["fr"]["video"], LANGUAGES["en"]["video"], LANGUAGES["fr"]["audio"], LANGUAGES["en"]["audio"]):
            # map to current language
            if "video" in current.lower() or "vidéo" in current.lower():
                self.type_option.set(self.trans["video"])
            else:
                self.type_option.set(self.trans["audio"])
        self.res_label.configure(text=self.trans["resolution"])
        self.download_button.configure(text=self.trans["start_download"])
        self.folder_button.configure(text=self.trans["choose_folder"])

    def choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.output_dir, title=self.trans["select_folder"])
        if selected:
            self.output_dir = selected
            self.folder_label.configure(text=self.output_dir)

    def append_status(self, text):
        self.status_box.insert("end", text + "\n")
        self.status_box.see("end")

    def poll_queues(self):
        # status queue
        try:
            while True:
                item = self.status_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "formats":
                    # got formats list
                    formats = item[1]
                    if formats:
                        labels = [desc for (_id, desc) in formats]
                        self.res_option.configure(values=labels)
                        self.res_option.set(labels[0])
                        self.append_status(self.trans["formats_loaded"])
                        # store formats locally
                        self._current_formats = {desc: fmt_id for (fmt_id, desc) in formats}
                    else:
                        self.append_status(self.trans["formats_loaded"] + " (0)")
                else:
                    # normal status text
                    self.append_status(item)
        except queue.Empty:
            pass
        # repeat
        self.after(400, self.poll_queues)

    def load_formats_for_first_link(self):
        text = self.links_box.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo(self.trans["error"], self.trans["no_links"])
            return
        first_link = text.splitlines()[0].strip()
        if not first_link:
            messagebox.showinfo(self.trans["error"], self.trans["no_links"])
            return

        # disable button while loading
        self.load_formats_btn.configure(state="disabled")
        self.append_status(self.trans["loading_formats"])
        t = threading.Thread(target=self._worker_load_formats, args=(first_link,))
        t.daemon = True
        t.start()

    def _worker_load_formats(self, url):
        try:
            formats = get_formats(url)
            self.status_queue.put(("formats", formats))
        except Exception as e:
            self.status_queue.put(f"{self.trans['error']} {e}")
        finally:
            # re-enable button in main thread (put a simple message to queue to run UI change)
            self.after(0, lambda: self.load_formats_btn.configure(state="normal"))

    def on_type_change(self, value):
        # if audio selected, disable resolution selector
        is_audio = (value == self.trans["audio"])
        if is_audio:
            self.res_option.configure(values=["-- audio uses bestaudio --"])
            self.res_option.set("-- audio uses bestaudio --")
        else:
            # if we have previously loaded formats, restore them:
            if hasattr(self, "_current_formats") and self._current_formats:
                labels = list(self._current_formats.keys())
                self.res_option.configure(values=labels)
                self.res_option.set(labels[0])
            else:
                self.res_option.configure(values=["Aucune (charger d'abord)"])
                self.res_option.set("Aucune (charger d'abord)")

    def start_download_thread(self):
        text = self.links_box.get("1.0", "end").strip()
        if not text:
            messagebox.showinfo(self.trans["error"], self.trans["no_links"])
            return
        urls = [u.strip() for u in text.splitlines() if u.strip()]
        if not urls:
            messagebox.showinfo(self.trans["error"], self.trans["no_links"])
            return

        # determine options
        is_audio = (self.type_option.get() == self.trans["audio"])
        chosen_res = self.res_option.get()
        fmt_id = None
        if not is_audio:
            if not chosen_res or "charger" in chosen_res.lower() or chosen_res.startswith("Aucune"):
                messagebox.showinfo(self.trans["error"], self.trans["no_format"])
                return
            # map label -> format_id
            fmt_id = getattr(self, "_current_formats", {}).get(chosen_res)
            if not fmt_id:
                # maybe label is of different language or previously loaded; try to parse first token
                fmt_id = chosen_res.split(" - ")[0]

        # start thread
        self.download_button.configure(state="disabled")
        t = threading.Thread(target=self._worker_batch_download, args=(urls, fmt_id, is_audio))
        t.daemon = True
        t.start()

    def _worker_batch_download(self, urls, fmt_id, is_audio):
        self.status_queue.put(self.trans["download_started"])
        for url in urls:
            # per-file progress hook
            def progress_hook(d):
                # d contains status, downloaded_bytes, total_bytes, eta, etc.
                status = d.get("status")
                if status == "downloading":
                    # build a short summary
                    downloaded = d.get("downloaded_bytes", 0)
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    if total:
                        pct = int(downloaded / total * 100)
                        self.status_queue.put(f"{url} — {pct}% ({downloaded}/{total} bytes)")
                    else:
                        self.status_queue.put(f"{url} — downloading ({downloaded} bytes)")
                elif status == "finished":
                    self.status_queue.put(f"{url} — finished, processing...")
                elif status == "error":
                    self.status_queue.put(f"{url} — error during download")

            try:
                self.status_queue.put(f"---- {url} ----")
                download_one(url, format_id=fmt_id, audio_only=is_audio, outdir=self.output_dir, progress_hook=progress_hook)
                self.status_queue.put(f"{url} — {self.trans['download_finished']}")
            except Exception as e:
                self.status_queue.put(f"{self.trans['error']} {url} — {e}")

        self.status_queue.put(self.trans["download_finished"])
        # re-enable button
        self.after(0, lambda: self.download_button.configure(state="normal"))

if __name__ == "__main__":
    app = YTDownloaderApp()
    app.mainloop()
