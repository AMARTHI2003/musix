from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout
from utils.audio_player import player

Builder.load_string("""
<PlayerBar>:
    orientation: "vertical"
    size_hint_y: None
    height: "68dp" if root.song_title else "0dp"
    padding: "8dp", "4dp", "8dp", "4dp"
    md_bg_color: 0.07, 0.07, 0.07, 1  # Matches app background
    
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.24, 0.21, 0.34, 1  # Dark purple matching Spotify player
        radius: [8, 8, 8, 8]
        padding: "8dp", "4dp", "8dp", "0dp"
        spacing: 0

        MDBoxLayout:
            spacing: "12dp"
            
            # Thumbnail Image
            FitImage:
                source: root.song_thumbnail
                size_hint: None, None
                size: "40dp", "40dp"
                radius: [4, 4, 4, 4]
                pos_hint: {"center_y": .5}

            # Song Info
            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.6
                spacing: "2dp"
                padding: 0, "8dp"

                MDLabel:
                    text: root.song_title
                    font_style: "Title"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                    shorten: True
                    shorten_from: "right"

                MDLabel:
                    text: root.song_artist
                    font_style: "Body"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 0.8, 0.8, 0.8, 1
                    shorten: True
                    shorten_from: "right"

            # Controls
            MDBoxLayout:
                size_hint_x: 0.4
                spacing: "4dp"
                padding: 0, "4dp"
                
                MDIconButton:
                    icon: "monitor-speaker"
                    theme_icon_color: "Custom"
                    icon_color: 0.8, 0.8, 0.8, 1
                    icon_size: "20dp"

                MDIconButton:
                    icon: "plus-circle-outline"
                    theme_icon_color: "Custom"
                    icon_color: 0.8, 0.8, 0.8, 1
                    icon_size: "24dp"

                MDIconButton:
                    icon: "pause" if root.is_playing else "play"
                    theme_icon_color: "Custom"
                    icon_color: 1, 1, 1, 1
                    icon_size: "28dp"
                    on_release: root.toggle_play()

        # Progress Bar at the very bottom edge of the player box
        MDLinearProgressIndicator:
            id: progress_bar
            size_hint_y: None
            height: "2dp"
            value: root.progress_pct
            color: 1, 1, 1, 1
""")


class PlayerBar(MDBoxLayout):
    song_title = StringProperty("")
    song_artist = StringProperty("")
    song_thumbnail = StringProperty("")
    is_playing = BooleanProperty(False)
    progress_pct = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Bind to player state
        player.bind(title=self._on_title)
        player.bind(artist=self._on_artist)
        player.bind(thumbnail=self._on_thumbnail)
        player.bind(is_playing=self._on_playing)
        player.bind(position=self._on_position)

    def _on_title(self, instance, value):
        self.song_title = value

    def _on_artist(self, instance, value):
        self.song_artist = value
        
    def _on_thumbnail(self, instance, value):
        self.song_thumbnail = value

    def _on_playing(self, instance, value):
        self.is_playing = value

    def _on_position(self, instance, value):
        if player.duration > 0:
            self.progress_pct = (value / player.duration) * 100
        else:
            self.progress_pct = 0

    def toggle_play(self):
        player.toggle_play()

    def next_track(self):
        player.next_track()

    def prev_track(self):
        player.prev_track()
