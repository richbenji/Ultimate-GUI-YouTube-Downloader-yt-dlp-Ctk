import yt_dlp
from .errors import InvalidURLError, VideoInfoFetchError


def extract_playlist_entries(url):
    """
    Extrait les vidéos d'une URL (playlist ou vidéo unique).

    Retourne une liste de dicts:
    [
        {"url": "...", "title": "...", "index": ...},
        ...
    ]

    Raises:
        InvalidURLError: Si l'URL est vide ou invalide
        VideoInfoFetchError: Si l'extraction échoue
    """
    # Validation basique
    if not url or not isinstance(url, str) or not url.strip():
        raise InvalidURLError()

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "no_warnings": True,
        "ignoreerrors": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise VideoInfoFetchError()

        # Cas 1 : Vidéo unique
        if info.get("_type") != "playlist":
            video_url = info.get("webpage_url") or info.get("url") or url
            video_title = info.get("title")

            if not video_title:
                raise VideoInfoFetchError()

            return [{
                "url": video_url,
                "title": video_title,
                "index": 1
            }]

        # Cas 2 : Playlist
        entries = []
        raw_entries = info.get("entries", [])

        if not raw_entries:
            raise VideoInfoFetchError()

        for idx, entry in enumerate(raw_entries, start=1):
            if not entry:
                continue

            # Construire l'URL complète de la vidéo
            video_url = entry.get("url")
            if not video_url:
                video_id = entry.get("id")
                if video_id:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    continue

            video_title = entry.get("title")
            if not video_title:
                video_title = f"Vidéo {idx}"

            entries.append({
                "url": video_url,
                "title": video_title,
                "index": idx
            })

        if not entries:
            raise VideoInfoFetchError()

        return entries

    except (InvalidURLError, VideoInfoFetchError):
        # Re-lever nos propres exceptions
        raise
    except Exception:
        # Toute autre erreur = problème d'extraction
        raise VideoInfoFetchError()


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