from yt_dlp import YoutubeDL
from tabulate import tabulate  # pip install tabulate

# URL de la vidéo YouTube
video_url = input("Entrez l'URL de la vidéo YouTube : ").strip()

# Options yt-dlp
ydl_opts = {'quiet': True, 'skip_download': True}

with YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(video_url, download=False)
    #print(info)  # Affiche toutes les informations de la vidéo

    # Affichage lisible des informations
    print("=== Informations Générales ===")
    print(f"Titre       : {info.get('title')}")
    print(f"Auteur      : {info.get('uploader')}")
    print(f"ID          : {info.get('id')}")
    print(f"Date upload : {info.get('upload_date')}")
    print(f"URL         : {info.get('webpage_url')}")


    def format_duration(seconds):
        if seconds is None:
            return "N/A"
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"  # format heures:minutes:secondes
        else:
            return f"{m:02d}:{s:02d}"  # format minutes:secondes si moins d’1h


    duration_sec = info.get("duration")
    print(f"Durée       : {format_duration(duration_sec)} ({duration_sec} secondes)")
    print(f"Vues        : {info.get('view_count')}")
    print(f"Likes       : {info.get('like_count')}")
    print(f"Description : {info.get('description')[:200]}...")  # Première partie de la description

    print(f"=== Infos vidéo : {info.get('title')} ===\n")

    table = []
    headers = ["Type", "Resolution", "Bitrate (kbps)", "Ext", "Filesize", "FPS", "Codec", "Format", "Format ID",
               "Protocole"]

    best_video = None
    best_audio = None
    max_vbr = 0
    max_abr = 0

    for f in info.get('formats', []):
        format_id = f.get('format_id')
        ext = f.get('ext')
        resolution = f.get('resolution') or (f"{f.get('height')}p" if f.get('height') else "")
        fps = f.get('fps') or ""

        # fusion codec
        vcodec = f.get('vcodec')
        acodec = f.get('acodec')
        codec = f"{vcodec or 'none'} / {acodec or 'none'}"

        # type du flux
        if vcodec != "none" and acodec != "none":
            flux_type = "Muxé"
        elif vcodec != "none":
            flux_type = "Vidéo seule"
        elif acodec != "none":
            flux_type = "Audio seule"
        else:
            flux_type = "Autre"

        # fusion bitrate
        vbr = f.get('vbr')
        abr = f.get('abr')
        tbr = f.get('tbr')
        bitrate_parts = []
        if vbr: bitrate_parts.append(f"v:{vbr}")
        if abr: bitrate_parts.append(f"a:{abr}")
        if tbr: bitrate_parts.append(f"t:{tbr}")
        bitrate = " / ".join(bitrate_parts) if bitrate_parts else ""

        # filesize
        filesize = f.get('filesize') or f.get('filesize_approx') or ""
        if isinstance(filesize, (int, float)):
            filesize = f"{round(filesize / (1024 * 1024), 2)} MB"

        format_note = f.get('format') or ""
        protocole = f.get('protocol') or ""

        table.append([flux_type, resolution, bitrate, ext, filesize, fps, codec, format_note, protocole, format_id])

        # Identifier le meilleur format vidéo (sans audio)
        vbr_val = f.get('vbr') or 0
        if vbr_val > max_vbr and f.get('vcodec') != 'none':
            max_vbr = vbr_val
            best_video = f
        # Identifier le meilleur format audio (sans vidéo)
        abr_val = f.get('abr') or 0
        if abr_val > max_abr and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
            max_abr = abr_val
            best_audio = f


    # fonction pour convertir "1080p" en nombre 1080 pour trier
    def res_to_int(res):
        if res and res.endswith("p"):
            try:
                return int(res.replace("p", ""))
            except:
                return 0
        return 0


    # ordre de priorité pour les types
    type_order = {"Muxé": 0, "Vidéo seule": 1, "Audio seule": 2, "Autre": 3}


    # tri : type > résolution > bitrate
    def sort_key(row):
        flux_type, _, _, resolution, _, _, bitrate, _, _, _ = row
        # extraire bitrate total si présent (sinon 0)
        br_val = 0
        for part in str(bitrate).split("/"):
            if "t:" in part:
                try:
                    br_val = int(float(part.split(":")[1]))
                except:
                    pass
        return (
            type_order.get(flux_type, 99),
            -res_to_int(resolution),
            -br_val
        )

    table.sort(key=sort_key)

    print(tabulate(table, headers=headers, tablefmt="grid"))

    print("\n=== Meilleur format vidéo seule ===")
    if best_video:
        print(
            f"Format ID: {best_video.get('format_id')}, Résolution: {best_video.get('resolution')}, Vidéo BR: {best_video.get('vbr')} kbps, Extension: {best_video.get('ext')}")

    print("\n=== Meilleur format audio seule ===")
    if best_audio:
        print(
            f"Format ID: {best_audio.get('format_id')},"
            f"Audio BR: {best_audio.get('abr')} kbps,"
            f"Extension: {best_audio.get('ext')}")