import yt_dlp
from .errors import InvalidURLError, VideoInfoFetchError


def extract_playlist_entries(url, cookies_path=None):
    """
    Extrait les vidéos d'une URL YouTube (vidéo unique ou playlist).

    - Gère playlists publiques
    - Gère playlists privées via cookies.txt
    - Distingue playlist privée / erreur réelle

    Retourne une liste de dicts :
    [
        {"url": "...", "title": "...", "index": ...},
        ...
    ]
    """

    # Validation basique
    if not url or not isinstance(url, str) or not url.strip():
        raise InvalidURLError()

    # 🔹 BASE OPTIONS
    base_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "ignoreerrors": False,
    }

    # 🔹 STRATÉGIES D’AUTHENTIFICATION (dans l’ordre)
    strategies = [
        # 1️⃣ Automatique : navigateur
        {
            **base_opts,
            "extract_flat": True,
            "cookiesfrombrowser": ("firefox",),
        },

        # 2️⃣ Manuel : cookies.txt
        {
            **base_opts,
            "extract_flat": False,
            "cookiefile": cookies_path,
        } if cookies_path else None,
    ]

    for ydl_opts in filter(None, strategies):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                continue

            # 🎥 Vidéo unique
            if info.get("_type") != "playlist":
                title = info.get("title")
                video_url = info.get("webpage_url")

                if not title or not video_url:
                    continue

                return [{
                    "url": video_url,
                    "title": title,
                    "index": 1
                }]

            # 📋 Playlist
            raw_entries = info.get("entries")

            if not raw_entries:
                continue

            entries = []
            for idx, entry in enumerate(raw_entries, start=1):
                if not entry:
                    continue

                video_id = entry.get("id")
                title = entry.get("title") or f"Vidéo {idx}"

                if not video_id:
                    continue

                entries.append({
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": title,
                    "index": idx
                })

            if entries:
                return entries

        except Exception:
            # On tente la stratégie suivante
            continue

    # ❌ Aucune stratégie n’a fonctionné
    raise VideoInfoFetchError("playlist_private")

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