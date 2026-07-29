from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from utils.api_client import api

Builder.load_string("""
<LoginScreen>:
    md_bg_color: 1, 1, 1, 1  # White background
    
    MDBoxLayout:
        orientation: "vertical"
        padding: "32dp"
        spacing: "24dp"
        pos_hint: {"center_x": .5, "center_y": .5}
        adaptive_height: True
        
        # Logo Area
        MDBoxLayout:
            size_hint: None, None
            size: "120dp", "120dp"
            pos_hint: {"center_x": .5}
            md_bg_color: 1, 1, 1, 1
            radius: [60, 60, 60, 60]
            
            canvas.before:
                Color:
                    rgba: 0.8, 0.2, 0.5, 1  # Pinkish gradient start approximation
                Line:
                    width: 2.5
                    circle: (self.center_x, self.center_y, 58)
                    
            MDIcon:
                icon: "music-note"
                theme_icon_color: "Custom"
                icon_color: 0.3, 0.2, 0.8, 1
                font_size: "64dp"
                pos_hint: {"center_x": .5, "center_y": .5}
                
        # Spacing
        Widget:
            size_hint_y: None
            height: "16dp"
            
        # Email Field
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "56dp"
            md_bg_color: 0.96, 0.96, 0.96, 1
            radius: [16, 16, 16, 16]
            padding: "16dp", "0dp", "16dp", "0dp"
            
            MDIcon:
                icon: "email"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.4, 0.4, 1
                pos_hint: {"center_y": .5}
                
            MDTextField:
                id: email_input
                hint_text: "Email"
                mode: "filled"
                theme_text_color: "Custom"
                text_color_normal: 0, 0, 0, 1
                hint_text_color_normal: 0.6, 0.6, 0.6, 1
                fill_color_normal: 0, 0, 0, 0
                active_line: False
                pos_hint: {"center_y": .5}

        # Password Field
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "56dp"
            md_bg_color: 0.96, 0.96, 0.96, 1
            radius: [16, 16, 16, 16]
            padding: "16dp", "0dp", "16dp", "0dp"
            
            MDIcon:
                icon: "lock"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.4, 0.4, 1
                pos_hint: {"center_y": .5}
                
            MDTextField:
                id: password_input
                hint_text: "Password"
                password: True
                mode: "filled"
                theme_text_color: "Custom"
                text_color_normal: 0, 0, 0, 1
                hint_text_color_normal: 0.6, 0.6, 0.6, 1
                fill_color_normal: 0, 0, 0, 0
                active_line: False
                pos_hint: {"center_y": .5}
                
            MDIconButton:
                icon: "eye-off"
                theme_icon_color: "Custom"
                icon_color: 0.4, 0.4, 0.4, 1
                pos_hint: {"center_y": .5}
                
        # Forgot password text
        MDLabel:
            text: "Forgot password?"
            halign: "right"
            font_style: "Label"
            role: "medium"
            theme_text_color: "Custom"
            text_color: 0.6, 0.6, 0.6, 1
            size_hint_y: None
            height: "24dp"
                
        # Login Button
        MDButton:
            style: "filled"
            md_bg_color: 0.05, 0.1, 0.2, 1  # Dark blue
            size_hint_x: 1
            height: "56dp"
            on_release: root.do_login()
            
            MDButtonText:
                text: "Login"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                font_style: "Title"
                role: "small"
                pos_hint: {"center_x": .5, "center_y": .5}
                
        # Spacing
        Widget:
            size_hint_y: None
            height: "32dp"
                
        # Signup text
        MDLabel:
            text: "Don't have an account? [b]Signup[/b]"
            markup: True
            halign: "center"
            font_style: "Label"
            role: "large"
            theme_text_color: "Custom"
            text_color: 0.4, 0.4, 0.4, 1
            
        MDLabel:
            id: status_label
            text: ""
            theme_text_color: "Error"
            halign: "center"
""")

class LoginScreen(MDScreen):
    def do_login(self):
        email = self.ids.email_input.text.strip()
        # The backend expects 'name' and 'email'. We'll use the email prefix as name.
        name = email.split('@')[0] if '@' in email else "User"
        
        if not email:
            self.ids.status_label.text = "Please enter an email."
            return
            
        self.ids.status_label.text = "Logging in..."
        api.login(name, email, callback=self.on_login_result)
        
    def on_login_result(self, data):
        Clock.schedule_once(lambda dt: self.handle_result(data))
        
    def handle_result(self, data):
        if data and "access_token" in data:
            self.manager.current = "app"
            try:
                with open("token.txt", "w") as f:
                    f.write(data["access_token"])
            except Exception:
                pass
        else:
            self.ids.status_label.text = "Login failed. Please try again."
