from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText
from utils.api_client import api

Builder.load_string("""
<LibraryScreen>:
    md_bg_color: 0.07, 0.07, 0.07, 1

    MDBoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "12dp"

        # Header
        MDBoxLayout:
            size_hint_y: None
            height: "56dp"

            MDLabel:
                text: "Your Library"
                font_style: "Headline"
                role: "small"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                bold: True

        # Create Playlist Button
        MDButton:
            style: "filled"
            md_bg_color: 0.6, 0.2, 0.8, 1
            size_hint_y: None
            height: "48dp"
            size_hint_x: 1
            on_release: root.show_create_dialog()

            MDButtonText:
                text: "Create New Playlist"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1

        # Playlists List
        MDLabel:
            text: "Your Playlists"
            font_style: "Title"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 1
            bold: True
            size_hint_y: None
            height: "32dp"

        ScrollView:
            MDList:
                id: playlists_list

                MDListItem:
                    md_bg_color: 0.12, 0.12, 0.12, 1
                    radius: [12, 12, 12, 12]

                    MDListItemHeadlineText:
                        text: "Liked Songs"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1

                    MDListItemSupportingText:
                        text: "Your favorite tracks"
                        theme_text_color: "Custom"
                        text_color: 0.7, 0.7, 0.7, 1
""")


class LibraryScreen(MDScreen):
    def on_enter(self):
        pass  # Playlists will be loaded when auth is implemented

    def show_create_dialog(self):
        from kivymd.uix.dialog import (
            MDDialog, MDDialogHeadlineText, MDDialogContentContainer,
            MDDialogButtonContainer
        )
        from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
        from kivymd.uix.button import MDButton, MDButtonText

        self._playlist_field = MDTextField(mode="outlined", size_hint_y=None, height="56dp")
        self._playlist_field.add_widget(MDTextFieldHintText(text="Playlist name"))

        dialog = MDDialog(
            MDDialogHeadlineText(text="New Playlist"),
            MDDialogContentContainer(self._playlist_field, orientation="vertical", padding="24dp"),
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=lambda x: dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Create"),
                    style="filled",
                    on_release=lambda x: self._create_playlist(dialog),
                ),
                spacing="8dp",
            ),
        )
        dialog.open()

    def _create_playlist(self, dialog):
        name = self._playlist_field.text.strip()
        if name:
            api.create_playlist(name, callback=lambda data: print(f"Created: {data}"))
        dialog.dismiss()
