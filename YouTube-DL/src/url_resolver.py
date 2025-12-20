"""
Couche métier : résolution d'URL YouTube (vidéo ou playlist)

- Valide l'URL
- Détecte playlist / vidéo
- Centralise TOUTES les erreurs liées à l'URL
- Ne dépend PAS de l'UI
"""

from .playlist_utils import extract_playlist_entries
from .errors import InvalidURLError


class UrlResolveError(Exception):
    """
    Exception métier unique pour l'UI.
    message_key correspond à une clé de traduction.
    """
    def __init__(self, message_key: str):
        self.message_key = message_key
        super().__init__(message_key)


def resolve_url(url: str):
    """
    Résout une URL YouTube et retourne une liste d'entrées vidéo.

    Chaque entrée est un dict (tel que retourné par extract_playlist_entries).

    Raises
    ------
    UrlResolveError
        - enter_valid_url : URL vide ou invalide
        - fetching_impossible : échec récupération infos
    """

    # 🔴 Validation unique de l'URL
    if not url or not isinstance(url, str) or not url.strip():
        raise UrlResolveError("enter_valid_url")

    try:
        entries = extract_playlist_entries(url)

    except InvalidURLError:
        # URL mal formée / non reconnue
        raise UrlResolveError("enter_valid_url")

    except Exception:
        # Erreur réseau, yt-dlp, parsing, etc.
        raise UrlResolveError("fetching_impossible")

    # Sécurité supplémentaire
    if not entries:
        raise UrlResolveError("fetching_impossible")

    return entries
