# Audio Player Manager
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty, ListProperty, DictProperty
)


class AudioPlayer(EventDispatcher):
    """Centralized audio player with state management."""

    # Observable properties
    title = StringProperty("")
    artist = StringProperty("")
    thumbnail = StringProperty("")
    video_id = StringProperty("")
    duration = NumericProperty(0)
    position = NumericProperty(0)
    is_playing = BooleanProperty(False)
    volume = NumericProperty(1.0)
    queue = ListProperty([])
    queue_index = NumericProperty(-1)
    current_song_data = DictProperty({})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sound = None
        self._update_event = None
        self._cache_dir = None

    @property
    def cache_dir(self):
        """Resolved lazily on first use, since this singleton is created at
        module-import time — before HarmonyApp.run() exists — so
        App.get_running_app() is always None if resolved in __init__."""
        if self._cache_dir is None:
            import os
            from kivy.app import App
            app = App.get_running_app()
            if app:
                self._cache_dir = os.path.join(app.user_data_dir, ".audio_cache")
            else:
                self._cache_dir = os.path.join(os.path.dirname(__file__), "..", ".audio_cache")
            os.makedirs(self._cache_dir, exist_ok=True)
        return self._cache_dir

    def play_song(self, song):
        """Play a song by downloading it to cache first."""
        self.stop()
        self.current_song_data = song

        self.title = song.get("title", "Unknown") + " (Downloading...)"
        self.artist = song.get("artist", "Unknown Artist")
        self.thumbnail = song.get("thumbnail", "")
        self.video_id = song.get("id", "")
        self.duration = song.get("duration", 0)
        self.position = 0

        from utils.api_client import api
        api.download_song(self.video_id, self.cache_dir, callback=self._on_download_complete)

    def _on_download_complete(self, local_path):
        Clock.schedule_once(lambda dt: self._start_playback(local_path))

    def _start_playback(self, local_path):
        # Remove the (Downloading...) suffix
        if self.title.endswith(" (Downloading...)"):
            self.title = self.title[:-17]
            
        if not local_path:
            self.title = "Download failed"
            return

        try:
            self._sound = SoundLoader.load(local_path)
            if self._sound:
                self._sound.volume = self.volume
                self._sound.play()
                self.is_playing = True
                self._update_event = Clock.schedule_interval(self._update_position, 0.5)
            else:
                self.title = "Playback failed"
        except Exception as e:
            print(f"Audio error: {e}")

    def _update_position(self, dt):
        if self._sound and self.is_playing:
            pos = self._sound.get_pos()
            if pos is not None:
                self.position = pos
            # Check if song finished
            length = self._sound.length
            if length and pos and pos >= length - 0.5:
                self.next_track()

    def toggle_play(self):
        """Toggle play/pause."""
        if not self._sound:
            return
        if self.is_playing:
            self._sound.stop()
            self.is_playing = False
            if self._update_event:
                self._update_event.cancel()
        else:
            self._sound.play()
            self.is_playing = True
            self._update_event = Clock.schedule_interval(self._update_position, 0.5)

    def stop(self):
        """Stop playback and cleanup."""
        if self._sound:
            self._sound.stop()
            self._sound.unload()
            self._sound = None
        self.is_playing = False
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

    def seek(self, position):
        """Seek to a position in seconds."""
        if self._sound:
            self._sound.seek(position)
            self.position = position

    def set_volume(self, vol):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, vol))
        if self._sound:
            self._sound.volume = self.volume

    def set_queue(self, songs, start_index=0):
        """Set the play queue and start playing from index."""
        self.queue = list(songs)
        self.queue_index = start_index

    def next_track(self):
        """Play the next track in queue."""
        if self.queue and self.queue_index < len(self.queue) - 1:
            self.queue_index += 1
            song = self.queue[self.queue_index]
            self.play_song(song)

    def prev_track(self):
        """Play the previous track in queue."""
        if self.queue and self.queue_index > 0:
            self.queue_index -= 1
            song = self.queue[self.queue_index]
            self.play_song(song)

    def format_time(self, seconds):
        """Format seconds into MM:SS."""
        if not seconds or seconds < 0:
            return "0:00"
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"


# Singleton
player = AudioPlayer()
