import yt_dlp
from yt_dlp.utils import DownloadError

from .errors import InvalidURLError, VideoInfoFetchError
from .settings import ENABLE_PRIVATE_PLAYLISTS, COOKIES_FILE


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

    ydl_opts = {
        "quiet": True,
        #"extract_flat": True,
        "skip_download": True,
        "no_warnings": True,
        "ignoreerrors": False,  # ⚠️ important pour playlists privées partielles
        #"cookiesfrombrowser": ("firefox",),
    }

    # 🔐 Cookies fournis dynamiquement par l'UI
    if cookies_path:
        ydl_opts["cookiefile"] = cookies_path
    # 🔐 Cookies globaux (option B)
    elif ENABLE_PRIVATE_PLAYLISTS and COOKIES_FILE.exists():
        ydl_opts["cookiefile"] = str(COOKIES_FILE)

    # 🔐 Playlist privée → extraction complète
    if ydl_opts.get("cookiefile"):
        ydl_opts["extract_flat"] = False
    else:
        ydl_opts["extract_flat"] = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise VideoInfoFetchError("fetching_impossible")

        # 🎥 CAS 1 : Vidéo unique
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

        # 📋 CAS 2 : Playlist
        raw_entries = info.get("entries")

        # Playlist privée ou inaccessible
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

    # 🔑 ERREUR yt-dlp (clé de la robustesse)
    except DownloadError as e:
        msg = str(e)

        # YouTube MENT : ce message apparaît aussi pour playlists privées
        if "The playlist does not exist" in msg:
            raise VideoInfoFetchError("playlist_private")

        raise VideoInfoFetchError("fetching_impossible")

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