"""
Fichier de traductions pour Ultimate GUI YouTube Downloader
Organisé par catégories logiques
"""


def get_text(key, lang="fr", **kwargs):
    """
    Récupère le texte traduit pour une clé donnée

    Args:
        key: Clé de traduction
        lang: Langue (fr ou en)
        **kwargs: Arguments pour le formatage des chaînes

    Returns:
        str: Texte traduit
    """
    try:
        text = TRANSLATIONS[lang].get(key, TRANSLATIONS["fr"].get(key, key))
        if kwargs:
            return text.format(**kwargs)
        return text
    except (KeyError, AttributeError):
        return key

TRANSLATIONS = {
    # ============================================================
    # 🇫🇷 FRANÇAIS
    # ============================================================
    "fr": {
        # ──────────────────────────────────────────────────────
        # EN-TÊTE APPLICATION
        # ──────────────────────────────────────────────────────
        "app_title": "Ultimate GUI YouTube Downloader",
        "app_subtitle": "Une interface graphique pour yt-dlp",

        # ──────────────────────────────────────────────────────
        # ONGLETS PRINCIPAUX
        # ──────────────────────────────────────────────────────
        "single_download_tab": "Téléchargement unique",
        "batch_download_tab": "Téléchargement par lot",
        "tutorial": "Tutoriel",

        # ──────────────────────────────────────────────────────
        # BOUTONS ET ACTIONS
        # ──────────────────────────────────────────────────────
        "check_button": "Ajouter",
        "download_button": "Télécharger",
        "cancel_button": "Annuler",
        "clear_queue": "Vider la file",
        "browse_button": "Parcourir",
        "load_from_file_button": "Charger depuis un fichier",
        "paste_multiple_urls": "Coller plusieurs URLs",
        "add_urls": "Ajouter",

        # ──────────────────────────────────────────────────────
        # CHAMPS ET LABELS
        # ──────────────────────────────────────────────────────
        "url_placeholder": "Collez l'URL YouTube ici",
        "paste_multiple_urls_hint": "Collez une URL par ligne :",
        "type_label": "Type :",
        "video_option": "Vidéo + Audio",
        "audio_only_option": "Audio uniquement",
        "resolution_label": "Résolution :",
        "audio_bitrate_label": "Bitrate audio :",
        "audio_format_label": "Format audio :",
        "output_folder_label": "Dossier de sortie :",
        "urls_list_label": "Liste des URLs YouTube (une par ligne) :",

        # ──────────────────────────────────────────────────────
        # INFORMATIONS VIDÉO
        # ──────────────────────────────────────────────────────
        "title": "Titre",
        "author": "Auteur",
        "upload_date": "Date de publication",
        "duration": "Durée",
        "views": "Vues",
        "likes": "Likes",
        "video_id": "ID vidéo",
        "url": "URL",
        "description": "Description",
        "no_description": "Aucune description.",
        "available_formats": "Formats disponibles",
        "best_video_format": "Meilleur format vidéo seule : ",
        "best_audio_format": "Meilleur format audio seul : ",

        # ──────────────────────────────────────────────────────
        # POPUP INFOS VIDÉO
        # ──────────────────────────────────────────────────────
        "video_info_title": "Informations vidéo",
        "text_summary": "Résumé texte",
        "tab": "Tableau",
        "detailed_summary": "Résumé détaillé",

        # ──────────────────────────────────────────────────────
        # STATUTS ET MESSAGES D'ÉTAT
        # ──────────────────────────────────────────────────────
        "ready_status": "Prêt",
        "loading_video_info": "Récupération des informations de la vidéo",
        "loading": "⏳ Chargement en cours...",
        "checking_url": "Vérification de l'URL...",
        "download_started": "Téléchargement démarré",
        "downloading": "Téléchargement :",
        "remaining_time": "Temps restant :",
        "processing_file": "Traitement du fichier...",
        "canceling_download": "Annulation du téléchargement...",
        "canceling_batch_download": "Annulation du téléchargement par lot...",
        "no_file_in_the_queue": "Aucun fichier dans la file d'attente",

        # ──────────────────────────────────────────────────────
        # PLAYLISTS
        # ──────────────────────────────────────────────────────
        "playlist_detected_singular": "📋 Playlist détectée : {count} vidéo trouvée. Chargement...",
        "playlist_detected_plural": "📋 Playlist détectée : {count} vidéos trouvées. Chargement...",
        "queue_added_singular": "✅ {count} vidéo ajoutée à la file d'attente",
        "queue_added_plural": "✅ {count} vidéos ajoutées à la file d'attente",

        # ──────────────────────────────────────────────────────
        # MESSAGES DE SUCCÈS
        # ──────────────────────────────────────────────────────
        "download_complete": "Téléchargement terminé",
        "download_complete_message": "Le téléchargement a été complété avec succès !",
        "batch_download_complete": "Téléchargement par lot terminé",
        "downloads_success_ratio_singular": "✅ {success}/{total} téléchargement réussi",
        "downloads_success_ratio_plural": "✅ {success}/{total} téléchargements réussis",

        # ──────────────────────────────────────────────────────
        # MESSAGES D'ERREUR ET AVERTISSEMENTS
        # ──────────────────────────────────────────────────────
        "warning": "Attention",
        "error": "Erreur",
        "error_prefix": "Erreur : ",
        "download_failed": "Échec du téléchargement",
        "download_canceled": "Téléchargement annulé",
        "partial_download_message": "Certains fichiers n'ont pas été téléchargés",
        "enter_valid_url": "Veuillez entrer une URL valide",
        "no_valid_urls": "Aucune URL valide trouvée",
        "no_video": "Aucune vidéo trouvée dans cette URL",
        "no_resolutions_found": "Pas de résolutions trouvées",
        "no_bitrates_found": "Pas de bitrates trouvées",
        "fetching_impossible": "Impossible d'obtenir les informations de la vidéo",
        "playlist_private": "Playlist privée — connexion requise. Veuillez fournir des cookies YouTube.",

        # ──────────────────────────────────────────────────────
        # FICHIERS
        # ──────────────────────────────────────────────────────
        "select_output_folder": "Sélectionner un dossier de sortie",
        "select_cookies_file": "Sélectionner le fichier cookies.txt",
        "load_urls_list": "Charger une liste d'URLs",
        "text_files": "Fichiers texte",
        "loaded_urls": "Chargé {count} URLs depuis le fichier",
        "file_load_error": "Erreur lors du chargement du fichier : {error}",
        "cannot_read_file": "Impossible de lire le fichier : {error}",
        "download_folder": "Téléchargements",
    },

    # ============================================================
    # 🇬🇧 ENGLISH
    # ============================================================
    "en": {
        # ──────────────────────────────────────────────────────
        # APPLICATION HEADER
        # ──────────────────────────────────────────────────────
        "app_title": "Ultimate GUI YouTube Downloader",
        "app_subtitle": "A yt-dlp GUI",

        # ──────────────────────────────────────────────────────
        # MAIN TABS
        # ──────────────────────────────────────────────────────
        "single_download_tab": "Single Download",
        "batch_download_tab": "Batch Download",
        "tutorial": "Tutorial",

        # ──────────────────────────────────────────────────────
        # BUTTONS AND ACTIONS
        # ──────────────────────────────────────────────────────
        "check_button": "Add",
        "download_button": "Download",
        "cancel_button": "Cancel",
        "clear_queue": "Clear queue",
        "browse_button": "Browse",
        "load_from_file_button": "Load from file",
        "paste_multiple_urls": "Paste multiple URLs",
        "add_urls": "Add",

        # ──────────────────────────────────────────────────────
        # FIELDS AND LABELS
        # ──────────────────────────────────────────────────────
        "url_placeholder": "Paste YouTube URL here",
        "paste_multiple_urls_hint": "Paste one URL per line:",
        "type_label": "Type:",
        "video_option": "Video + Audio",
        "audio_only_option": "Audio only",
        "resolution_label": "Resolution:",
        "audio_bitrate_label": "Audio bitrate:",
        "audio_format_label": "Audio format:",
        "output_folder_label": "Output folder:",
        "urls_list_label": "YouTube URLs list (one per line):",

        # ──────────────────────────────────────────────────────
        # VIDEO INFORMATION
        # ──────────────────────────────────────────────────────
        "title": "Title",
        "author": "Author",
        "upload_date": "Upload date",
        "duration": "Duration",
        "views": "Views",
        "likes": "Likes",
        "video_id": "Video ID",
        "url": "URL",
        "description": "Description",
        "no_description": "No description.",
        "available_formats": "Available formats",
        "best_video_format": "Best video-only format: ",
        "best_audio_format": "Best audio-only format: ",

        # ──────────────────────────────────────────────────────
        # VIDEO INFO POPUP
        # ──────────────────────────────────────────────────────
        "video_info_title": "Video information",
        "text_summary": "Text summary",
        "tab": "Table",
        "detailed_summary": "Detailed summary",

        # ──────────────────────────────────────────────────────
        # STATUS AND STATE MESSAGES
        # ──────────────────────────────────────────────────────
        "ready_status": "Ready",
        "loading_video_info": "Fetching video information",
        "loading": "⏳ Loading...",
        "checking_url": "Checking URL...",
        "download_started": "Download started",
        "downloading": "Downloading:",
        "remaining_time": "Remaining time:",
        "processing_file": "Processing file...",
        "canceling_download": "Canceling download...",
        "canceling_batch_download": "Canceling batch download...",
        "no_file_in_the_queue": "No file in the queue",

        # ──────────────────────────────────────────────────────
        # PLAYLISTS
        # ──────────────────────────────────────────────────────
        "playlist_detected_singular": "📋 Playlist detected: {count} video found. Loading...",
        "playlist_detected_plural": "📋 Playlist detected: {count} videos found. Loading...",
        "queue_added_singular": "✅ {count} video added to queue",
        "queue_added_plural": "✅ {count} videos added to queue",

        # ──────────────────────────────────────────────────────
        # SUCCESS MESSAGES
        # ──────────────────────────────────────────────────────
        "download_complete": "Download Complete",
        "download_complete_message": "Download completed successfully!",
        "batch_download_complete": "Batch Download Complete",
        "downloads_success_ratio_singular": "✅ {success}/{total} download successful",
        "downloads_success_ratio_plural": "✅ {success}/{total} downloads successful",

        # ──────────────────────────────────────────────────────
        # ERROR AND WARNING MESSAGES
        # ──────────────────────────────────────────────────────
        "warning": "Warning",
        "error": "Error",
        "error_prefix": "Error: ",
        "download_failed": "Download failed",
        "download_canceled": "Download canceled",
        "partial_download_message": "Some files were not downloaded",
        "enter_valid_url": "Please enter a valid URL",
        "no_valid_urls": "No valid URLs found",
        "no_video": "No video found at this URL",
        "no_resolutions_found": "No resolutions found",
        "no_bitrates_found": "No bitrates found",
        "fetching_impossible": "Unable to obtain video information",
        "playlist_private": "Private playlist — login required. Please provide YouTube cookies.",

        # ──────────────────────────────────────────────────────
        # FILES
        # ──────────────────────────────────────────────────────
        "select_output_folder": "Select output folder",
        "select_cookies_file": "Select cookies.txt file",
        "load_urls_list": "Load URLs list",
        "text_files": "Text files",
        "loaded_urls": "Loaded {count} URLs from file",
        "file_load_error": "Error loading file: {error}",
        "cannot_read_file": "Cannot read file: {error}",
        "download_folder": "Downloads",
    },

    # ============================================================
    # 🇪🇸 ESPAÑOL
    # ============================================================
    "es": {
        # ──────────────────────────────────────────────────────
        # ENCABEZADO DE APLICACIÓN
        # ──────────────────────────────────────────────────────
        "app_title": "Ultimate GUI YouTube Downloader",
        "app_subtitle": "Una interfaz gráfica para yt-dlp",

        # ──────────────────────────────────────────────────────
        # PESTAÑAS PRINCIPALES
        # ──────────────────────────────────────────────────────
        "single_download_tab": "Descarga única",
        "batch_download_tab": "Descarga por lotes",
        "tutorial": "Tutorial",

        # ──────────────────────────────────────────────────────
        # BOTONES Y ACCIONES
        # ──────────────────────────────────────────────────────
        "check_button": "Añadir",
        "download_button": "Descargar",
        "cancel_button": "Cancelar",
        "clear_queue": "Vaciar cola",
        "browse_button": "Explorar",
        "load_from_file_button": "Cargar desde archivo",
        "paste_multiple_urls": "Pegar varias URLs",
        "add_urls": "Añadir",

        # ──────────────────────────────────────────────────────
        # CAMPOS Y ETIQUETAS
        # ──────────────────────────────────────────────────────
        "url_placeholder": "Pega la URL de YouTube aquí",
        "paste_multiple_urls_hint": "Pega una URL por línea:",
        "type_label": "Tipo:",
        "video_option": "Vídeo + Audio",
        "audio_only_option": "Solo audio",
        "resolution_label": "Resolución:",
        "audio_bitrate_label": "Bitrate de audio:",
        "audio_format_label": "Formato de audio:",
        "output_folder_label": "Carpeta de destino:",
        "urls_list_label": "Lista de URLs de YouTube (una por línea):",

        # ──────────────────────────────────────────────────────
        # INFORMACIÓN DEL VÍDEO
        # ──────────────────────────────────────────────────────
        "title": "Título",
        "author": "Autor",
        "upload_date": "Fecha de publicación",
        "duration": "Duración",
        "views": "Vistas",
        "likes": "Me gusta",
        "video_id": "ID del vídeo",
        "url": "URL",
        "description": "Descripción",
        "no_description": "Sin descripción.",
        "available_formats": "Formatos disponibles",
        "best_video_format": "Mejor formato solo vídeo: ",
        "best_audio_format": "Mejor formato solo audio: ",

        # ──────────────────────────────────────────────────────
        # POPUP DE INFO DE VÍDEO
        # ──────────────────────────────────────────────────────
        "video_info_title": "Información del vídeo",
        "text_summary": "Resumen de texto",
        "tab": "Tabla",
        "detailed_summary": "Resumen detallado",

        # ──────────────────────────────────────────────────────
        # ESTADO Y MENSAJES DE ESTADO
        # ──────────────────────────────────────────────────────
        "ready_status": "Listo",
        "loading_video_info": "Obteniendo información del vídeo",
        "loading": "⏳ Cargando...",
        "checking_url": "Verificando URL...",
        "download_started": "Descarga iniciada",
        "downloading": "Descargando:",
        "remaining_time": "Tiempo restante:",
        "processing_file": "Procesando archivo...",
        "canceling_download": "Cancelando descarga...",
        "canceling_batch_download": "Cancelando descarga por lotes...",
        "no_file_in_the_queue": "No hay archivos en la cola",

        # ──────────────────────────────────────────────────────
        # LISTAS DE REPRODUCCIÓN
        # ──────────────────────────────────────────────────────
        "playlist_detected_singular": "📋 Lista de reproducción detectada: {count} vídeo encontrado. Cargando...",
        "playlist_detected_plural": "📋 Lista de reproducción detectada: {count} vídeos encontrados. Cargando...",
        "queue_added_singular": "✅ {count} vídeo añadido a la cola",
        "queue_added_plural": "✅ {count} vídeos añadidos a la cola",

        # ──────────────────────────────────────────────────────
        # MENSAJES DE ÉXITO
        # ──────────────────────────────────────────────────────
        "download_complete": "Descarga completa",
        "download_complete_message": "¡La descarga se completó correctamente!",
        "batch_download_complete": "Descarga por lotes completada",
        "downloads_success_ratio_singular": "✅ {success}/{total} descarga exitosa",
        "downloads_success_ratio_plural": "✅ {success}/{total} descargas exitosas",

        # ──────────────────────────────────────────────────────
        # MENSAJES DE ERROR Y ADVERTENCIA
        # ──────────────────────────────────────────────────────
        "warning": "Advertencia",
        "error": "Error",
        "error_prefix": "Error: ",
        "download_failed": "Error en la descarga",
        "download_canceled": "Descarga cancelada",
        "partial_download_message": "Algunos archivos no se descargaron",
        "enter_valid_url": "Por favor, introduce una URL válida",
        "no_valid_urls": "No se encontraron URLs válidas",
        "no_video": "No se encontró ningún vídeo en esta URL",
        "no_resolutions_found": "No se encontraron resoluciones",
        "no_bitrates_found": "No se encontraron bitrates",
        "fetching_impossible": "No es posible obtener la información del vídeo",
        "playlist_private": "Lista de reproducción privada — inicio de sesión requerido. Proporcione cookies de YouTube.",

        # ──────────────────────────────────────────────────────
        # ARCHIVOS
        # ──────────────────────────────────────────────────────
        "select_output_folder": "Seleccionar carpeta de destino",
        "select_cookies_file": "Seleccionar archivo cookies.txt",
        "load_urls_list": "Cargar lista de URLs",
        "text_files": "Archivos de texto",
        "loaded_urls": "Cargadas {count} URLs desde el archivo",
        "file_load_error": "Error al cargar el archivo: {error}",
        "cannot_read_file": "No se puede leer el archivo: {error}",
        "download_folder": "Descargas",
    },

    # ============================================================
    # 🇮🇹 ITALIANO
    # ============================================================
    "it": {
        # ──────────────────────────────────────────────────────
        # INTESTAZIONE APPLICAZIONE
        # ──────────────────────────────────────────────────────
        "app_title": "Ultimate GUI YouTube Downloader",
        "app_subtitle": "Un'interfaccia grafica per yt-dlp",

        # ──────────────────────────────────────────────────────
        # SCHEDE PRINCIPALI
        # ──────────────────────────────────────────────────────
        "single_download_tab": "Download singolo",
        "batch_download_tab": "Download multiplo",
        "tutorial": "Tutorial",

        # ──────────────────────────────────────────────────────
        # PULSANTI E AZIONI
        # ──────────────────────────────────────────────────────
        "check_button": "Aggiungi",
        "download_button": "Scarica",
        "cancel_button": "Annulla",
        "clear_queue": "Svuota coda",
        "browse_button": "Sfoglia",
        "load_from_file_button": "Carica da file",
        "paste_multiple_urls": "Incolla più URL",
        "add_urls": "Aggiungi",

        # ──────────────────────────────────────────────────────
        # CAMPI ED ETICHETTE
        # ──────────────────────────────────────────────────────
        "url_placeholder": "Incolla l'URL di YouTube qui",
        "paste_multiple_urls_hint": "Incolla un URL per riga:",
        "type_label": "Tipo:",
        "video_option": "Video + Audio",
        "audio_only_option": "Solo audio",
        "resolution_label": "Risoluzione:",
        "audio_bitrate_label": "Bitrate audio:",
        "audio_format_label": "Formato audio:",
        "output_folder_label": "Cartella di destinazione:",
        "urls_list_label": "Elenco di URL YouTube (uno per riga):",

        # ──────────────────────────────────────────────────────
        # INFORMAZIONI VIDEO
        # ──────────────────────────────────────────────────────
        "title": "Titolo",
        "author": "Autore",
        "upload_date": "Data di pubblicazione",
        "duration": "Durata",
        "views": "Visualizzazioni",
        "likes": "Mi piace",
        "video_id": "ID video",
        "url": "URL",
        "description": "Descrizione",
        "no_description": "Nessuna descrizione.",
        "available_formats": "Formati disponibili",
        "best_video_format": "Miglior formato solo video: ",
        "best_audio_format": "Miglior formato solo audio: ",

        # ──────────────────────────────────────────────────────
        # POPUP INFO VIDEO
        # ──────────────────────────────────────────────────────
        "video_info_title": "Informazioni sul video",
        "text_summary": "Riepilogo testuale",
        "tab": "Tabella",
        "detailed_summary": "Riepilogo dettagliato",

        # ──────────────────────────────────────────────────────
        # STATO E MESSAGGI DI STATO
        # ──────────────────────────────────────────────────────
        "ready_status": "Pronto",
        "loading_video_info": "Recupero delle informazioni dal video",
        "loading": "⏳ Caricamento...",
        "checking_url": "Verifica dell'URL in corso...",
        "download_started": "Download avviato",
        "downloading": "Scaricamento:",
        "remaining_time": "Tempo rimanente:",
        "processing_file": "Elaborazione file...",
        "canceling_download": "Annullamento del download...",
        "canceling_batch_download": "Annullamento del download multiplo...",
        "no_file_in_the_queue": "Nessun file nella coda",

        # ──────────────────────────────────────────────────────
        # PLAYLIST
        # ──────────────────────────────────────────────────────
        "playlist_detected_singular": "📋 Playlist rilevata: {count} video trovato. Caricamento...",
        "playlist_detected_plural": "📋 Playlist rilevata: {count} video trovati. Caricamento...",
        "queue_added_singular": "✅ {count} video aggiunto alla coda",
        "queue_added_plural": "✅ {count} video aggiunti alla coda",

        # ──────────────────────────────────────────────────────
        # MESSAGGI DI SUCCESSO
        # ──────────────────────────────────────────────────────
        "download_complete": "Download completato",
        "download_complete_message": "Il download è stato completato con successo!",
        "batch_download_complete": "Download multiplo completato",
        "downloads_success_ratio_singular": "✅ {success}/{total} download riuscito",
        "downloads_success_ratio_plural": "✅ {success}/{total} download riusciti",

        # ──────────────────────────────────────────────────────
        # MESSAGGI DI ERRORE E AVVISO
        # ──────────────────────────────────────────────────────
        "warning": "Attenzione",
        "error": "Errore",
        "error_prefix": "Errore: ",
        "download_failed": "Download fallito",
        "download_canceled": "Download annullato",
        "partial_download_message": "Alcuni file non sono stati scaricati",
        "enter_valid_url": "Inserisci un URL valido",
        "no_valid_urls": "Nessun URL valido trovato",
        "no_video": "Nessun video trovato in questo URL",
        "no_resolutions_found": "Nessuna risoluzione trovata",
        "no_bitrates_found": "Nessun bitrate trovato",
        "fetching_impossible": "Impossibile ottenere le informazioni del video",
        "playlist_private": "Playlist privata — accesso richiesto. Fornire i cookie di YouTube.",

        # ──────────────────────────────────────────────────────
        # FILE
        # ──────────────────────────────────────────────────────
        "select_output_folder": "Seleziona cartella di destinazione",
        "select_cookies_file": "Seleziona file cookies.txt",
        "load_urls_list": "Carica elenco di URL",
        "text_files": "File di testo",
        "loaded_urls": "Caricate {count} URL dal file",
        "file_load_error": "Errore durante il caricamento del file: {error}",
        "cannot_read_file": "Impossibile leggere il file: {error}",
        "download_folder": "Scaricati",
    },

    # ============================================================
    # 🇩🇪 DEUTSCH
    # ============================================================
    "de": {
        # ──────────────────────────────────────────────────────
        # ANWENDUNGS-KOPFZEILE
        # ──────────────────────────────────────────────────────
        "app_title": "Ultimate GUI YouTube Downloader",
        "app_subtitle": "Eine grafische Oberfläche für yt-dlp",

        # ──────────────────────────────────────────────────────
        # HAUPTREGISTERKARTEN
        # ──────────────────────────────────────────────────────
        "single_download_tab": "Einzeldownload",
        "batch_download_tab": "Stapel-Download",
        "tutorial": "Anleitung",

        # ──────────────────────────────────────────────────────
        # SCHALTFLÄCHEN UND AKTIONEN
        # ──────────────────────────────────────────────────────
        "check_button": "Hinzufügen",
        "download_button": "Herunterladen",
        "cancel_button": "Abbrechen",
        "clear_queue": "Warteschlange leeren",
        "browse_button": "Durchsuchen",
        "load_from_file_button": "Aus Datei laden",
        "paste_multiple_urls": "Mehrere URLs einfügen",
        "add_urls": "Hinzufügen",

        # ──────────────────────────────────────────────────────
        # FELDER UND BESCHRIFTUNGEN
        # ──────────────────────────────────────────────────────
        "url_placeholder": "Füge die YouTube-URL hier ein",
        "paste_multiple_urls_hint": "Füge eine URL pro Zeile ein:",
        "type_label": "Typ:",
        "video_option": "Video + Audio",
        "audio_only_option": "Nur Audio",
        "resolution_label": "Auflösung:",
        "audio_bitrate_label": "Audio-Bitrate:",
        "audio_format_label": "Audio-Format:",
        "output_folder_label": "Zielordner:",
        "urls_list_label": "Liste der YouTube-URLs (eine pro Zeile):",

        # ──────────────────────────────────────────────────────
        # VIDEO-INFORMATIONEN
        # ──────────────────────────────────────────────────────
        "title": "Titel",
        "author": "Autor",
        "upload_date": "Veröffentlichungsdatum",
        "duration": "Dauer",
        "views": "Aufrufe",
        "likes": "Likes",
        "video_id": "Video-ID",
        "url": "URL",
        "description": "Beschreibung",
        "no_description": "Keine Beschreibung.",
        "available_formats": "Verfügbare Formate",
        "best_video_format": "Bestes reines Videoformat: ",
        "best_audio_format": "Bestes reines Audioformat: ",

        # ──────────────────────────────────────────────────────
        # VIDEO-INFO-POPUP
        # ──────────────────────────────────────────────────────
        "video_info_title": "Video-Informationen",
        "text_summary": "Textzusammenfassung",
        "tab": "Tabelle",
        "detailed_summary": "Detaillierte Zusammenfassung",

        # ──────────────────────────────────────────────────────
        # STATUS UND STATUSMELDUNGEN
        # ──────────────────────────────────────────────────────
        "ready_status": "Bereit",
        "loading_video_info": "Video-Informationen werden abgerufen",
        "loading": "⏳ Wird geladen...",
        "checking_url": "URL wird überprüft...",
        "download_started": "Download gestartet",
        "downloading": "Herunterladen:",
        "remaining_time": "Verbleibende Zeit:",
        "processing_file": "Datei wird verarbeitet...",
        "canceling_download": "Download wird abgebrochen...",
        "canceling_batch_download": "Stapel-Download wird abgebrochen...",
        "no_file_in_the_queue": "Keine Datei in der Warteschlange",

        # ──────────────────────────────────────────────────────
        # WIEDERGABELISTEN
        # ──────────────────────────────────────────────────────
        "playlist_detected_singular": "📋 Wiedergabeliste erkannt: {count} Video gefunden. Wird geladen...",
        "playlist_detected_plural": "📋 Wiedergabeliste erkannt: {count} Videos gefunden. Wird geladen...",
        "queue_added_singular": "✅ {count} Video zur Warteschlange hinzugefügt",
        "queue_added_plural": "✅ {count} Videos zur Warteschlange hinzugefügt",

        # ──────────────────────────────────────────────────────
        # ERFOLGSMELDUNGEN
        # ──────────────────────────────────────────────────────
        "download_complete": "Download abgeschlossen",
        "download_complete_message": "Der Download wurde erfolgreich abgeschlossen!",
        "batch_download_complete": "Stapel-Download abgeschlossen",
        "downloads_success_ratio_singular": "✅ {success}/{total} Download erfolgreich",
        "downloads_success_ratio_plural": "✅ {success}/{total} Downloads erfolgreich",

        # ──────────────────────────────────────────────────────
        # FEHLER- UND WARNMELDUNGEN
        # ──────────────────────────────────────────────────────
        "warning": "Warnung",
        "error": "Fehler",
        "error_prefix": "Fehler: ",
        "download_failed": "Download fehlgeschlagen",
        "download_canceled": "Download abgebrochen",
        "partial_download_message": "Einige Dateien wurden nicht heruntergeladen",
        "enter_valid_url": "Bitte geben Sie eine gültige URL ein",
        "no_valid_urls": "Keine gültigen URLs gefunden",
        "no_video": "Kein Video unter dieser URL gefunden",
        "no_resolutions_found": "Keine Auflösungen gefunden",
        "no_bitrates_found": "Keine Bitraten gefunden",
        "fetching_impossible": "Video-Informationen können nicht abgerufen werden",
        "playlist_private": "Private Wiedergabeliste — Anmeldung erforderlich. Bitte YouTube-Cookies bereitstellen.",

        # ──────────────────────────────────────────────────────
        # DATEIEN
        # ──────────────────────────────────────────────────────
        "select_output_folder": "Zielordner auswählen",
        "select_cookies_file": "cookies.txt-Datei auswählen",
        "load_urls_list": "URL-Liste laden",
        "text_files": "Textdateien",
        "loaded_urls": "{count} URLs aus Datei geladen",
        "file_load_error": "Fehler beim Laden der Datei: {error}",
        "cannot_read_file": "Datei kann nicht gelesen werden: {error}",
        "download_folder": "Downloads",
    },
}