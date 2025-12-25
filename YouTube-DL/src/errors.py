# src/errors.py

class InvalidURLError(Exception):
    """URL absente ou invalide (erreur utilisateur)."""
    pass


class VideoInfoFetchError(Exception):
    """Échec lors de la récupération des infos via yt-dlp."""
    pass

class VideoInfoFetchError(Exception):
    def __init__(self, message_key="fetching_impossible"):
        self.message_key = message_key
        super().__init__(message_key)
