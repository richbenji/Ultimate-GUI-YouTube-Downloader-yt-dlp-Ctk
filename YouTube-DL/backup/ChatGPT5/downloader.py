# downloader.py
import yt_dlp

def get_formats(url, max_formats=100):
    """
    Retourne une liste de tuples (format_id, description)
    description: ex. "136 - 1280x720 - mp4"
    """
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        seen = set()
        for f in info.get("formats", [])[:max_formats]:
            fmt_id = f.get("format_id")
            # composer une description utile
            resolution = f.get("resolution") or f.get("height") or ""
            ext = f.get("ext") or ""
            # Avoid duplicates (same id)
            if fmt_id in seen:
                continue
            seen.add(fmt_id)
            desc = f"{fmt_id} - {resolution} - {ext}"
            formats.append((fmt_id, desc))
        return formats

def download_one(url, format_id=None, audio_only=False, outdir=".", progress_hook=None):
    """
    Télécharge une seule URL.
    - format_id: str or None. if audio_only True -> uses 'bestaudio/best'
    - progress_hook: callable(d) where d is dict from yt_dlp progress
    """
    ydl_opts = {
        "outtmpl": f"{outdir}/%(title)s - %(id)s.%(ext)s",
        "progress_hooks": [progress_hook] if progress_hook else [],
        "quiet": True,
        "noplaylist": True
    }

    if audio_only:
        # extract audio and keep original audio
        ydl_opts["format"] = "bestaudio/best"
        # optionally, could add postprocessors to convert to mp3, but let's keep original
    else:
        if format_id:
            ydl_opts["format"] = format_id
        else:
            ydl_opts["format"] = "bestvideo+bestaudio/best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
