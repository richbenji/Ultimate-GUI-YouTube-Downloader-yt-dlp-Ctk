import yt_dlp
from tabulate import tabulate  # pip install tabulate


class VideoInfo:
    def __init__(self, url):
        self.url = url
        self.title = ""
        self.uploader = ""
        self.video_id = ""
        self.upload_date = ""
        self.view_count = 0
        self.like_count = 0
        self.description = ""
        self.resolutions = []
        self.duration = 0
        self.thumbnail = ""
        self.formats = []
        self.audio_bitrates = []
        self.is_valid = False

    def fetch_info(self):
        """Récupère toutes les infos de la vidéo via yt_dlp"""
        try:
            ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

                # Infos générales
                self.title = info.get("title", "Unknown Title")
                self.uploader = info.get("uploader", "")
                self.video_id = info.get("id", "")
                self.upload_date = info.get("upload_date", "")
                self.view_count = info.get("view_count", 0)
                self.like_count = info.get("like_count", 0)
                self.description = info.get("description", "")
                self.duration = info.get("duration", 0)
                self.thumbnail = info.get("thumbnail", "")
                self.formats = info.get("formats", [])

                # Résolutions disponibles
                video_formats = [f for f in self.formats if f.get("ext") == "mp4" and f.get("height") is not None]
                resolutions = {f"{f['height']}p" for f in video_formats if f.get("height")}
                self.resolutions = sorted(resolutions, key=lambda x: int(x[:-1]), reverse=True)

                # Bitrates audio réels
                audio_formats = [f for f in self.formats if f.get("acodec") != "none" and f.get("abr")]
                bitrates = {round(f["abr"]) for f in audio_formats if f.get("abr")}
                self.audio_bitrates = sorted(bitrates, reverse=True)

                self.is_valid = True
                return True
        except Exception as e:
            print(f"Erreur lors de l'extraction des informations: {e}")
            return False

    def get_detailed_summary(self):
        """Retourne un résumé détaillé avec un tableau des formats."""

        def format_duration(seconds):
            if seconds is None:
                return "N/A"
            seconds = int(seconds)
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            if h > 0:
                return f"{h:02d}:{m:02d}:{s:02d}"
            else:
                return f"{m:02d}:{s:02d}"

        lines = []
        lines.append("=== Informations Générales ===")
        lines.append(f"Titre       : {self.title}")
        lines.append(f"Auteur      : {self.uploader}")
        lines.append(f"ID          : {self.video_id}")
        lines.append(f"Date upload : {self.upload_date}")
        lines.append(f"URL         : {self.url}")
        lines.append(f"Durée       : {format_duration(self.duration)} ({self.duration} sec)")
        lines.append(f"Vues        : {self.view_count}")
        lines.append(f"Likes       : {self.like_count}")
        desc = self.description or ""
        lines.append(f"Description : {desc[:200]}...")

        lines.append(f"\n=== Infos vidéo : {self.title} ===\n")

        table = []
        headers = [
            "Type", "Resolution", "Bitrate (kbps)", "Ext",
            "Filesize", "FPS", "Codec", "Format", "Format ID", "Protocole"
        ]

        best_video = None
        best_audio = None
        max_vbr = 0
        max_abr = 0

        for f in self.formats or []:
            format_id = f.get("format_id")
            ext = f.get("ext")
            resolution = f.get("resolution") or (f"{f.get('height')}p" if f.get("height") else "")
            fps = f.get("fps") or ""

            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            codec = f"{vcodec or 'none'} / {acodec or 'none'}"

            if vcodec != "none" and acodec != "none":
                flux_type = "Muxé"
            elif vcodec != "none":
                flux_type = "Vidéo seule"
            elif acodec != "none":
                flux_type = "Audio seule"
            else:
                flux_type = "Autre"

            vbr = f.get("vbr")
            abr = f.get("abr")
            tbr = f.get("tbr")
            bitrate_parts = []
            if vbr: bitrate_parts.append(f"v:{vbr}")
            if abr: bitrate_parts.append(f"a:{abr}")
            if tbr: bitrate_parts.append(f"t:{tbr}")
            bitrate = " / ".join(bitrate_parts) if bitrate_parts else ""

            filesize = f.get("filesize") or f.get("filesize_approx") or ""
            if isinstance(filesize, (int, float)):
                filesize = f"{round(filesize / (1024 * 1024), 2)} MB"

            format_note = f.get("format") or ""
            protocole = f.get("protocol") or ""

            table.append([
                flux_type, resolution, bitrate, ext, filesize, fps,
                codec, format_note, format_id, protocole
            ])

            vbr_val = f.get("vbr") or 0
            if vbr_val > max_vbr and f.get("vcodec") != "none":
                max_vbr = vbr_val
                best_video = f

            abr_val = f.get("abr") or 0
            if abr_val > max_abr and f.get("acodec") != "none" and f.get("vcodec") == "none":
                max_abr = abr_val
                best_audio = f

        # tri
        def res_to_int(res):
            if res and res.endswith("p"):
                try:
                    return int(res.replace("p", ""))
                except:
                    return 0
            return 0

        type_order = {"Muxé": 0, "Vidéo seule": 1, "Audio seule": 2, "Autre": 3}

        def sort_key(row):
            flux_type, resolution, bitrate, *_ = row
            br_val = 0
            for part in str(bitrate).split("/"):
                if "t:" in part:
                    try:
                        br_val = int(float(part.split(":")[1]))
                    except:
                        pass
            return (
                type_order.get(flux_type, 99),
                -res_to_int(resolution),
                -br_val
            )

        table.sort(key=sort_key)
        lines.append(tabulate(table, headers=headers, tablefmt="grid"))

        if best_video:
            lines.append("\n=== Meilleur format vidéo seule ===")
            lines.append(
                f"Format ID: {best_video.get('format_id')}, "
                f"Résolution: {best_video.get('resolution')}, "
                f"Vidéo BR: {best_video.get('vbr')} kbps, "
                f"Extension: {best_video.get('ext')}"
            )

        if best_audio:
            lines.append("\n=== Meilleur format audio seule ===")
            lines.append(
                f"Format ID: {best_audio.get('format_id')}, "
                f"Audio BR: {best_audio.get('abr')} kbps, "
                f"Extension: {best_audio.get('ext')}"
            )

        return "\n".join(lines)

    def get_table_data(self):
        """Retourne (headers, rows) pour un affichage Treeview."""
        headers = [
            "Type", "Resolution", "Bitrate (kbps)", "Ext",
            "Filesize", "FPS", "Codec", "Format", "Format ID", "Protocole"
        ]

        rows = []
        for f in self.formats or []:
            format_id = f.get("format_id")
            ext = f.get("ext")
            resolution = f.get("resolution") or (f"{f.get('height')}p" if f.get("height") else "")
            fps = f.get("fps") or ""

            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            codec = f"{vcodec or 'none'} / {acodec or 'none'}"

            if vcodec != "none" and acodec != "none":
                flux_type = "Muxé"
            elif vcodec != "none":
                flux_type = "Vidéo seule"
            elif acodec != "none":
                flux_type = "Audio seule"
            else:
                flux_type = "Autre"

            bitrate_parts = []
            if f.get("vbr"): bitrate_parts.append(f"v:{f['vbr']}")
            if f.get("abr"): bitrate_parts.append(f"a:{f['abr']}")
            if f.get("tbr"): bitrate_parts.append(f"t:{f['tbr']}")
            bitrate = " / ".join(bitrate_parts)

            filesize = f.get("filesize") or f.get("filesize_approx") or ""
            if isinstance(filesize, (int, float)):
                filesize = f"{round(filesize / (1024*1024), 2)} MB"

            rows.append([
                flux_type, resolution, bitrate, ext, filesize, fps,
                codec, f.get("format") or "", format_id, f.get("protocol") or ""
            ])

        return headers, rows
