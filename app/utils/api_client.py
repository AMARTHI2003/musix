# API Client for Harmony Music Backend
import requests
import threading
from kivy.utils import platform

if platform == "android":
    BASE_URL = "http://10.0.2.2:8000"  # Android emulator -> host machine
else:
    BASE_URL = "http://localhost:8000"  # Desktop dev

class HarmonyAPI:
    """Async-friendly API client for the Harmony Music backend."""

    def __init__(self):
        self.base_url = BASE_URL
        self.token = None

    def set_token(self, token):
        self.token = token

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ───── Search ─────
    def search(self, query, callback=None):
        """Search for songs. Runs in background thread, calls callback with results."""
        def _do():
            try:
                resp = requests.get(
                    f"{self.base_url}/songs/search",
                    params={"q": query},
                    timeout=25,
                )
                results = resp.json() if resp.status_code == 200 else []
            except Exception as e:
                print(f"Search error: {e}")
                results = []
            if callback:
                callback(results)
        threading.Thread(target=_do, daemon=True).start()

    # ───── Download Song ─────
    def download_song(self, video_id, cache_dir, callback=None):
        """Download song to local cache for stable playback."""
        import os
        def _do():
            local_path = os.path.join(cache_dir, f"{video_id}.m4a")
            if os.path.exists(local_path) and os.path.getsize(local_path) > 1024:
                # Already cached
                if callback:
                    callback(local_path)
                return
                
            try:
                resp = requests.get(
                    f"{self.base_url}/songs/stream/{video_id}.m4a",
                    stream=True,
                    timeout=30
                )
                if resp.status_code == 200:
                    with open(local_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                    if callback:
                        callback(local_path)
                else:
                    if callback:
                        callback(None)
            except Exception as e:
                print(f"Download error: {e}")
                if callback:
                    callback(None)
                    
        threading.Thread(target=_do, daemon=True).start()

    # ───── Auth ─────
    def login(self, name, email, callback=None):
        def _do():
            try:
                resp = requests.post(
                    f"{self.base_url}/auth/custom_login",
                    json={"name": name, "email": email},
                    timeout=10,
                )
                data = resp.json() if resp.status_code == 200 else None
                if data and "access_token" in data:
                    self.set_token(data["access_token"])
            except Exception as e:
                print(f"Login error: {e}")
                data = None
            if callback:
                callback(data)
        threading.Thread(target=_do, daemon=True).start()

    def get_profile(self, callback=None):
        def _do():
            try:
                resp = requests.get(
                    f"{self.base_url}/auth/me",
                    headers=self._headers(),
                    timeout=10,
                )
                data = resp.json() if resp.status_code == 200 else None
            except Exception:
                data = None
            if callback:
                callback(data)
        threading.Thread(target=_do, daemon=True).start()

    # ───── Favorites ─────
    def toggle_favorite(self, song, callback=None):
        def _do():
            try:
                resp = requests.post(
                    f"{self.base_url}/playlists/favorites/toggle",
                    headers=self._headers(),
                    params={
                        "song_id": song["id"],
                        "title": song.get("title", ""),
                        "artist": song.get("artist", ""),
                        "thumbnail": song.get("thumbnail", ""),
                    },
                    timeout=10,
                )
                data = resp.json() if resp.status_code == 200 else None
            except Exception:
                data = None
            if callback:
                callback(data)
        threading.Thread(target=_do, daemon=True).start()

    # ───── Playlists ─────
    def get_playlists(self, callback=None):
        def _do():
            try:
                resp = requests.get(
                    f"{self.base_url}/playlists/",
                    headers=self._headers(),
                    timeout=10,
                )
                data = resp.json() if resp.status_code == 200 else []
            except Exception:
                data = []
            if callback:
                callback(data)
        threading.Thread(target=_do, daemon=True).start()

    def create_playlist(self, name, callback=None):
        def _do():
            try:
                resp = requests.post(
                    f"{self.base_url}/playlists/",
                    headers=self._headers(),
                    json={"name": name},
                    timeout=10,
                )
                data = resp.json() if resp.status_code == 200 else None
            except Exception:
                data = None
            if callback:
                callback(data)
        threading.Thread(target=_do, daemon=True).start()

    def add_song_to_playlist(self, playlist_id, song, callback=None):
        def _do():
            try:
                resp = requests.post(
                    f"{self.base_url}/playlists/{playlist_id}/songs/{song['id']}",
                    headers=self._headers(),
                    params={
                        "title": song.get("title", ""),
                        "artist": song.get("artist", ""),
                        "thumbnail": song.get("thumbnail", ""),
                        "duration": song.get("duration", 0),
                    },
                    timeout=10,
                )
                data = resp.json() if resp.status_code == 200 else None
            except Exception:
                data = None
            if callback:
                callback(data)
        threading.Thread(target=_do, daemon=True).start()

    # ───── Health Check ─────
    def health_check(self, callback=None):
        def _do():
            try:
                resp = requests.get(f"{self.base_url}/auth/health", timeout=5)
                ok = resp.status_code == 200
            except Exception:
                ok = False
            if callback:
                callback(ok)
        threading.Thread(target=_do, daemon=True).start()


# Singleton instance
api = HarmonyAPI()
