from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from utils.audio_player import player
from utils.api_client import api
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

Builder.load_string("""
#:import player utils.audio_player.player

<PlayerScreen>:
    md_bg_color: 0.1, 0.05, 0.15, 1
    
    MDBoxLayout:
        orientation: "vertical"
        padding: "24dp"
        spacing: "24dp"

        # Top Bar
        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            
            MDIconButton:
                icon: "chevron-down"
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1
                icon_size: "32dp"
                on_release: root.manager.current = "home"
                
            MDLabel:
                text: "Now Playing"
                halign: "center"
                font_style: "Title"
                role: "medium"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                bold: True
                
            MDIconButton:
                icon: "dots-vertical"
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1

        # Cover Art
        MDBoxLayout:
            size_hint_y: 0.5
            padding: "16dp"
            
            FitImage:
                source: player.thumbnail
                radius: [16, 16, 16, 16]
                
        # Song Info & Favorite
        MDBoxLayout:
            size_hint_y: None
            height: "80dp"
            
            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.8
                
                MDLabel:
                    text: player.title
                    font_style: "Headline"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                    shorten: True
                    shorten_from: "right"
                    
                MDLabel:
                    text: player.artist
                    font_style: "Title"
                    role: "medium"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.7, 0.7, 1
                    
            MDIconButton:
                icon: "heart" if root.is_favorite else "heart-outline"
                theme_icon_color: "Custom"
                icon_color: (0.1, 0.8, 0.3, 1) if root.is_favorite else (1, 1, 1, 1)
                icon_size: "32dp"
                pos_hint: {"center_y": .5}
                on_release: root.toggle_favorite()

        # Progress
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: "40dp"
            spacing: "8dp"
            
            MDLinearProgressIndicator:
                value: (player.position / player.duration * 100) if player.duration else 0
                color: 1, 1, 1, 1
                
            MDBoxLayout:
                MDLabel:
                    text: player.format_time(player.position)
                    font_style: "Label"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.7, 0.7, 1
                MDLabel:
                    text: player.format_time(player.duration)
                    halign: "right"
                    font_style: "Label"
                    role: "small"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.7, 0.7, 1
                    
        # Controls
        MDBoxLayout:
            size_hint_y: None
            height: "80dp"
            spacing: "16dp"
            
            MDIconButton:
                icon: "shuffle"
                theme_icon_color: "Custom"
                icon_color: 0.7, 0.7, 0.7, 1
                pos_hint: {"center_y": .5}
                
            MDIconButton:
                icon: "skip-previous"
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1
                icon_size: "48dp"
                pos_hint: {"center_y": .5}
                on_release: player.prev_track()
                
            MDIconButton:
                icon: "pause-circle" if player.is_playing else "play-circle"
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1
                icon_size: "72dp"
                pos_hint: {"center_y": .5}
                on_release: player.toggle_play()
                
            MDIconButton:
                icon: "skip-next"
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1
                icon_size: "48dp"
                pos_hint: {"center_y": .5}
                on_release: player.next_track()
                
            MDIconButton:
                icon: "repeat"
                theme_icon_color: "Custom"
                icon_color: 0.7, 0.7, 0.7, 1
                pos_hint: {"center_y": .5}
""")

class PlayerScreen(MDScreen):
    is_favorite = BooleanProperty(False)

    def toggle_favorite(self):
        song = player.current_song_data
        if not song:
            return
            
        api.toggle_favorite(song, callback=self.on_favorite_toggled)
        
    def on_favorite_toggled(self, data):
        def _update(dt):
            if data:
                self.is_favorite = data.get("is_favorite", False)
                MDSnackbar(
                    MDSnackbarText(text=data.get("message", "Updated favorites")),
                    y="24dp",
                    pos_hint={"center_x": 0.5},
                    size_hint_x=0.8,
                ).open()
        Clock.schedule_once(_update)
