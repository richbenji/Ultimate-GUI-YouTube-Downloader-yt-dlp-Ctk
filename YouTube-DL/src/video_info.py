import yt_dlp

class VideoInfo:
    def __init__(self, url):
        self.url = url
        self.title = ""
        self.resolutions = []
        self.duration = 0
        self.thumbnail = ""
        self.formats = []
        self.audio_bitrates = []
        self.is_valid = False

    def fetch_info(self):
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.title = info.get('title', 'Unknown Title')
                self.duration = info.get('duration', 0)
                self.thumbnail = info.get('thumbnail', '')
                self.formats = info.get('formats', [])

                video_formats = [f for f in self.formats if f.get('ext') == 'mp4' and f.get('height') is not None]
                resolutions = {f"{f['height']}p" for f in video_formats if f.get('height')}
                self.resolutions = sorted(resolutions, key=lambda x: int(x[:-1]), reverse=True)

                audio_formats = [f for f in self.formats if f.get('acodec') != 'none' and f.get('abr')]
                bitrates = {f['abr'] for f in audio_formats if f.get('abr')}
                self.audio_bitrates = sorted(bitrates, reverse=True)

                self.is_valid = True
                return True
        except Exception as e:
            print(f"Erreur lors de l'extraction des informations: {e}")
            return False
