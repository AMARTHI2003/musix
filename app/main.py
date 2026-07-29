"""
Harmony Music - A Premium Music Streaming Application
Built with Python, KivyMD, and FastAPI
"""

import os
from kivy.utils import platform

if platform != "android":
    os.environ["KIVY_AUDIO"] = "ffpyplayer"

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.navigationbar import (
    MDNavigationBar, MDNavigationItem, MDNavigationItemIcon, MDNavigationItemLabel
)
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.utils import platform

# Set window size for desktop testing
if platform not in ("android", "ios"):
    Window.size = (400, 750)

from screens.login_screen import LoginScreen
from screens.home_screen import HomeScreen
from screens.search_screen import SearchScreen
from screens.library_screen import LibraryScreen
from screens.player_screen import PlayerScreen
from components.player_bar import PlayerBar
from kivymd.uix.boxlayout import MDBoxLayout
from utils.api_client import api

Builder.load_string("""
<HarmonyApp>:

<RootScreenManager>:
    MDScreen:
        name: "app"
        
        MDBoxLayout:
            orientation: "vertical"
            md_bg_color: 0.07, 0.07, 0.07, 1

            MDScreenManager:
                id: tab_manager

                HomeScreen:
                    name: "home"

                SearchScreen:
                    name: "search"

                LibraryScreen:
                    name: "library"

            # Tapping the player bar opens the full PlayerScreen
            MDBoxLayout:
                size_hint_y: None
                height: player_bar.height
                
                ButtonBehaviorBox:
                    on_release: root.current = "player"
                    PlayerBar:
                        id: player_bar

            MDNavigationBar:
                id: nav_bar
                md_bg_color: 0.09, 0.09, 0.09, 1
                on_switch_tabs: root.on_tab_switch(*args)

                MDNavigationItem:
                    MDNavigationItemIcon:
                        icon: "home"
                    MDNavigationItemLabel:
                        text: "Home"

                MDNavigationItem:
                    MDNavigationItemIcon:
                        icon: "magnify"
                    MDNavigationItemLabel:
                        text: "Search"

                MDNavigationItem:
                    MDNavigationItemIcon:
                        icon: "playlist-music"
                    MDNavigationItemLabel:
                        text: "Your Library"

                MDNavigationItem:
                    MDNavigationItemIcon:
                        icon: "plus-box-outline"
                    MDNavigationItemLabel:
                        text: "Create"

    PlayerScreen:
        name: "player"
        
<ButtonBehaviorBox@ButtonBehavior+MDBoxLayout>:
    # Simple wrapper to make MDBoxLayout clickable
""")


class RootScreenManager(MDScreenManager):
    def on_tab_switch(self, bar, item, item_icon, item_text):
        tab_map = {
            "Home": "home",
            "Search": "search",
            "Your Library": "library",
            "Create": "home",
        }
        screen_name = tab_map.get(item_text, "home")
        self.ids.tab_manager.current = screen_name


class HarmonyApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Purple"
        self.title = "Harmony Music"
        
        sm = RootScreenManager()
        sm.current = "app"
        
        # Silently login as a guest to get a token for Favorites
        api.login("Guest", "guest@harmonymusic.app")
                    
        return sm


if __name__ == "__main__":
    HarmonyApp().run()
