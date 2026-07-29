[app]
title = Harmony Music
package.name = harmonymusic
package.domain = org.harmonymusic
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,otf,json
source.exclude_dirs = venv,.buildozer,.audio_cache,__pycache__,bin

version = 1.0.0

requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,pillow,urllib3,certifi,charset-normalizer,idna,pyjwt

# Android screen orientation
orientation = portrait

# Android permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Android API levels
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

# Only build for arm64 (faster build, covers modern phones)
android.archs = arm64-v8a

# Fullscreen
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
