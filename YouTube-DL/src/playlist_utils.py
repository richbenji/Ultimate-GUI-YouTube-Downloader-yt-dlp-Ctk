import yt_dlp
from .errors import InvalidURLError, VideoInfoFetchError
from .settings import ENABLE_PRIVATE_PLAYLISTS, COOKIES_FILE


def extract_playlist_entries(url):
    if not url or not isinstance(url, str) or not url.strip():
        raise InvalidURLError()

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "no_warnings": True,
        "ignoreerrors": True,  # ⚠️ important pour playlists privées partielles
        "cookiesfrombrowser": ("firefox",),
    }

    # 🔐 Support playlists privées
    if ENABLE_PRIVATE_PLAYLISTS and COOKIES_FILE.exists():
        ydl_opts["cookiefile"] = str(COOKIES_FILE)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise VideoInfoFetchError("fetching_impossible")

        # 🎥 Vidéo unique
        if info.get("_type") != "playlist":
            title = info.get("title")
            video_url = info.get("webpage_url")

            if not title or not video_url:
                raise VideoInfoFetchError("fetching_impossible")

            return [{
                "url": video_url,
                "title": title,
                "index": 1
            }]

        # 📋 Playlist
        raw_entries = info.get("entries")

        if raw_entries is None:
            raise VideoInfoFetchError("playlist_private")

        entries = []
        for idx, entry in enumerate(raw_entries, start=1):
            if not entry:
                continue  # vidéo privée / supprimée

            video_id = entry.get("id")
            title = entry.get("title") or f"Vidéo {idx}"

            if not video_id:
                continue

            entries.append({
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": title,
                "index": idx
            })

        if not entries:
            raise VideoInfoFetchError("playlist_private")

        return entries

    except VideoInfoFetchError:
        raise
    except Exception:
        raise VideoInfoFetchError("fetching_impossible")


def is_playlist_url(url):
    """
    Détecte si une URL est une playlist YouTube.

    Returns:
        bool: True si c'est une playlist, False sinon
    """
    if not url:
        return False

    playlist_indicators = [
        "playlist?list=",
        "&list=",
        "/playlist?",
    ]

    return any(indicator in url.lower() for indicator in playlist_indicators)