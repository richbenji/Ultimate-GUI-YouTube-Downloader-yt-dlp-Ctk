# src/errors.py

class InvalidURLError(Exception):
    """URL absente ou invalide (erreur utilisateur)."""
    pass


class VideoInfoFetchError(Exception):
    """Échec lors de la récupération des infos via yt-dlp."""
    pass
