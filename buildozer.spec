[app]
title = MC Mod Converter
package.name = mcmodconverter
package.domain = org.mcmodconverter
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.1.1,android,pyjnius
orientation = portrait
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a

[buildozer]
log_level = 2
