import yt_dlp


def extract_playlist_entries(url):
    """
    Extrait les vidéos d'une URL (playlist ou vidéo unique).

    Retourne une liste de dicts:
    [
        {"url": "...", "title": "...", "index": ...},
        ...
    ]

    Si l'URL est une vidéo unique, retourne une liste avec un seul élément.
    Si c'est une playlist, retourne toutes les vidéos de la playlist.
    """
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,  # Ne télécharge pas, juste les métadonnées
        "skip_download": True,
        "no_warnings": True,
        "ignoreerrors": True,  # Continue même si certaines vidéos échouent
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Cas 1 : Vidéo unique
        if info.get("_type") != "playlist":
            return [{
                "url": info.get("webpage_url") or info.get("url") or url,
                "title": info.get("title", "Titre inconnu"),
                "index": 1
            }]

        # Cas 2 : Playlist
        entries = []
        for idx, entry in enumerate(info.get("entries", []), start=1):
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

            entries.append({
                "url": video_url,
                "title": entry.get("title", f"Vidéo {idx}"),
                "index": idx
            })

        return entries

    except Exception as e:
        raise Exception(f"Impossible d'extraire les informations : {str(e)}")


def is_playlist_url(url):
    """
    Détecte si une URL est une playlist YouTube.

    Returns:
        bool: True si c'est une playlist, False sinon
    """
    playlist_indicators = [
        "playlist?list=",
        "&list=",
        "/playlist?",
    ]

    return any(indicator in url.lower() for indicator in playlist_indicators)