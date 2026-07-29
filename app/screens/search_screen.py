from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemLeadingAvatar
from utils.api_client import api
from utils.audio_player import player

Builder.load_string("""
<SearchScreen>:
    md_bg_color: 0.07, 0.07, 0.07, 1

    MDBoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "12dp"

        # Search Header
        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            spacing: "12dp"

            MDLabel:
                text: "Search"
                font_style: "Headline"
                role: "small"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                bold: True
                size_hint_x: None
                width: "100dp"

        # Search Input
        MDTextField:
            id: search_field
            mode: "outlined"
            size_hint_y: None
            height: "56dp"
            on_text_validate: root.do_search()

            MDTextFieldHintText:
                text: "What do you want to listen to?"

            MDTextFieldLeadingIcon:
                icon: "magnify"

        # Search Button
        MDButton:
            style: "filled"
            md_bg_color: 0.6, 0.2, 0.8, 1
            size_hint_x: 1
            size_hint_y: None
            height: "48dp"
            on_release: root.do_search()

            MDButtonText:
                text: "Search"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1

        # Loading indicator
        MDLabel:
            id: status_label
            text: ""
            halign: "center"
            font_style: "Body"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 0.6, 0.6, 0.6, 1
            size_hint_y: None
            height: "24dp"

        # Results
        ScrollView:
            MDList:
                id: results_list
""")


class SearchScreen(MDScreen):
    search_results = ListProperty([])

    def do_search(self):
        query = self.ids.search_field.text.strip()
        if not query:
            return

        self.ids.status_label.text = "Searching..."
        self.ids.results_list.clear_widgets()
        api.search(query, callback=self._on_results)

    def _on_results(self, results):
        self.search_results = results
        Clock.schedule_once(lambda dt: self._populate_results(results))

    def _populate_results(self, results):
        self.ids.results_list.clear_widgets()

        if not results:
            self.ids.status_label.text = "No results found"
            return

        self.ids.status_label.text = f"{len(results)} results"

        for i, song in enumerate(results):
            dur = int(song.get("duration") or 0)
            dur_str = f"{dur // 60}:{dur % 60:02d}" if dur else ""

            item = MDListItem(
                on_release=lambda x, s=song, idx=i: self._play_song(s, idx),
                md_bg_color=(0.12, 0.12, 0.12, 1),
                radius=[12, 12, 12, 12],
            )
            item.add_widget(MDListItemLeadingAvatar(source=song.get("thumbnail", "")))
            item.add_widget(MDListItemHeadlineText(
                text=song.get("title", "Unknown")[:60],
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
            ))
            item.add_widget(MDListItemSupportingText(
                text=f"{song.get('artist', 'Unknown')}  |  {dur_str}",
                theme_text_color="Custom",
                text_color=(0.7, 0.7, 0.7, 1),
            ))
            self.ids.results_list.add_widget(item)

    def _play_song(self, song, index):
        # Set queue to all search results, start from clicked index
        player.set_queue(self.search_results, index)
        player.play_song(song)
