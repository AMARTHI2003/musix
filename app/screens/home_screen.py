from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, DictProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from utils.api_client import api
from utils.audio_player import player

Builder.load_string("""
<MusicCard>:
    style: "filled"
    md_bg_color: 0, 0, 0, 0
    orientation: "vertical"
    size_hint: None, None
    size: "150dp", "210dp"
    spacing: "8dp"
    padding: 0
    
    FitImage:
        source: root.image_source
        size_hint_y: None
        height: "150dp"
        radius: [8, 8, 8, 8]
        
    MDLabel:
        text: root.title_text
        font_style: "Title"
        role: "medium"
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1
        bold: True
        shorten: True
        shorten_from: "right"
        size_hint_y: None
        height: "20dp"
        
    MDLabel:
        text: root.subtitle_text
        font_style: "Body"
        role: "small"
        theme_text_color: "Custom"
        text_color: 0.6, 0.6, 0.6, 1
        shorten: True
        shorten_from: "right"
        size_hint_y: None
        height: "20dp"

<HomeScreen>:
    md_bg_color: 0.07, 0.07, 0.07, 1

    ScrollView:
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            padding: "16dp"
            spacing: "24dp"

            # Header row (Avatar + Pills)
            MDBoxLayout:
                size_hint_y: None
                height: "40dp"
                spacing: "12dp"

                # Avatar
                MDBoxLayout:
                    size_hint: None, None
                    size: "40dp", "40dp"
                    md_bg_color: 0.8, 0.4, 0.6, 1
                    radius: [20, 20, 20, 20]
                    MDLabel:
                        text: "A"
                        halign: "center"
                        valign: "center"
                        font_style: "Title"
                        role: "medium"
                        theme_text_color: "Custom"
                        text_color: 0, 0, 0, 1
                        bold: True

                # Pills
                MDButton:
                    style: "filled"
                    md_bg_color: 0.1, 0.8, 0.3, 1
                    size_hint_y: None
                    height: "36dp"
                    pos_hint: {"center_y": .5}
                    MDButtonText:
                        text: "All"
                        theme_text_color: "Custom"
                        text_color: 0, 0, 0, 1
                        
                MDButton:
                    style: "filled"
                    md_bg_color: 0.2, 0.2, 0.2, 1
                    size_hint_y: None
                    height: "36dp"
                    pos_hint: {"center_y": .5}
                    MDButtonText:
                        text: "Music"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        
                MDButton:
                    style: "filled"
                    md_bg_color: 0.2, 0.2, 0.2, 1
                    size_hint_y: None
                    height: "36dp"
                    pos_hint: {"center_y": .5}
                    MDButtonText:
                        text: "Podcasts"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1

            # First Section: Trending (For fans of...)
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                spacing: "12dp"
                
                MDBoxLayout:
                    size_hint_y: None
                    height: "48dp"
                    spacing: "12dp"
                    
                    FitImage:
                        source: "https://i.ytimg.com/vi/bXa-wbiXiOw/hqdefault.jpg" # placeholder avatar
                        size_hint: None, None
                        size: "48dp", "48dp"
                        radius: [24, 24, 24, 24]
                        
                    MDBoxLayout:
                        orientation: "vertical"
                        MDLabel:
                            text: "For fans of"
                            font_style: "Body"
                            role: "small"
                            theme_text_color: "Custom"
                            text_color: 0.6, 0.6, 0.6, 1
                        MDLabel:
                            text: "Trending Music"
                            font_style: "Title"
                            role: "large"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            bold: True

                ScrollView:
                    do_scroll_y: False
                    do_scroll_x: True
                    bar_width: 0
                    size_hint_y: None
                    height: "210dp"
                    MDBoxLayout:
                        id: trending_row
                        orientation: "horizontal"
                        adaptive_width: True
                        spacing: "16dp"

            # Second Section: Popular Radio
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                spacing: "12dp"
                
                MDLabel:
                    text: "Popular radio"
                    font_style: "Title"
                    role: "large"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                    size_hint_y: None
                    height: "32dp"

                ScrollView:
                    do_scroll_y: False
                    do_scroll_x: True
                    bar_width: 0
                    size_hint_y: None
                    height: "210dp"
                    MDBoxLayout:
                        id: radio_row
                        orientation: "horizontal"
                        adaptive_width: True
                        spacing: "16dp"

            # Third Section: Top Mixes
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                spacing: "12dp"
                
                MDLabel:
                    text: "Your top mixes"
                    font_style: "Title"
                    role: "large"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                    size_hint_y: None
                    height: "32dp"

                ScrollView:
                    do_scroll_y: False
                    do_scroll_x: True
                    bar_width: 0
                    size_hint_y: None
                    height: "210dp"
                    MDBoxLayout:
                        id: mixes_row
                        orientation: "horizontal"
                        adaptive_width: True
                        spacing: "16dp"

            # Bottom padding to clear player bar and nav
            MDBoxLayout:
                size_hint_y: None
                height: "120dp"
""")


class MusicCard(MDCard):
    image_source = StringProperty("")
    title_text = StringProperty("")
    subtitle_text = StringProperty("")
    song_data = DictProperty({})

    def on_release(self):
        if self.song_data:
            player.play_song(self.song_data)


class HomeScreen(MDScreen):
    def on_enter(self):
        # Load multiple sections
        Clock.schedule_once(self.load_data, 0.1)

    def load_data(self, dt):
        api.search("trending music 2025", callback=self._on_trending)
        Clock.schedule_once(lambda dt: api.search("latest english pop songs 2025", callback=self._on_radio), 2)
        Clock.schedule_once(lambda dt: api.search("lofi hip hop mix", callback=self._on_mixes), 4)

    def _on_trending(self, results):
        Clock.schedule_once(lambda dt: self._populate_row(self.ids.trending_row, results))

    def _on_radio(self, results):
        Clock.schedule_once(lambda dt: self._populate_row(self.ids.radio_row, results))

    def _on_mixes(self, results):
        Clock.schedule_once(lambda dt: self._populate_row(self.ids.mixes_row, results))

    def _populate_row(self, row_widget, results):
        row_widget.clear_widgets()
        for song in results[:8]:
            card = MusicCard(
                image_source=song.get("thumbnail", ""),
                title_text=song.get("title", "Unknown"),
                subtitle_text=song.get("artist", "Unknown Artist"),
                song_data=song
            )
            row_widget.add_widget(card)
