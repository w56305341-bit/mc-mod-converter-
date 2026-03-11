# Minecraft Bedrock Mod Auto-Converter & Installer

Convert raw mod folders or ZIP files into valid `.mcaddon` / `.mcpack` files and install them directly into Minecraft PE — with one tap.

---

## Features

| Feature | Details |
|---|---|
| 📁 File Picker | Browse `.zip` or mod folders from Downloads |
| 📝 Auto Manifest | Generates `manifest.json` with unique UUID if missing |
| 📦 Packaging | Wraps files into proper `.mcaddon` / `.mcpack` archive |
| 🚀 One-Click Install | Opens Minecraft PE import dialog via Android Intent |
| 🔒 Scoped Storage | Works on Android 10 / 11 / 12 / 13 / 14 |
| 📋 Status Log | Live step-by-step feedback in the UI |

---

## Project Structure

```
mc_mod_converter/
├── main.py                    # App entry point (Kivy App class)
├── buildozer.spec             # APK build config
├── ui/
│   ├── __init__.py
│   └── main_screen.py         # Full UI (KivyMD Material Design)
├── utils/
│   ├── __init__.py
│   ├── converter.py           # Extraction → Manifest → Packaging engine
│   └── file_picker.py         # Android SAF / Scoped Storage file picker
└── assets/
    └── file_provider_paths.xml  # FileProvider config for Android 7+
```

---

## How to Build the APK

### Prerequisites

- **Linux** (Ubuntu 20.04 / 22.04 recommended) or WSL2
- Python 3.10+
- Java 11 (OpenJDK)

### Step 1 – Install Buildozer

```bash
pip install buildozer cython
sudo apt install -y git zip unzip openjdk-11-jdk \
    python3-dev libffi-dev libssl-dev \
    autoconf libtool pkg-config zlib1g-dev
```

### Step 2 – Build

```bash
cd mc_mod_converter
buildozer android debug
```

> First build downloads Android SDK/NDK (~1.5 GB). Takes 15–30 min.
> Subsequent builds are much faster.

### Step 3 – Install on Device

```bash
# With USB debugging enabled:
buildozer android deploy run
# OR copy the APK manually:
ls bin/*.apk
adb install bin/mcmodconverter-1.0.0-debug.apk
```

---

## How to Use the App

1. **Browse** – Tap "Browse File" and pick a `.zip` mod or select a folder.
2. **Format** – Choose `.mcaddon` (full add-on) or `.mcpack` (resource/behaviour only).
3. **Convert** – Tap "Convert Mod". The app will:
   - Extract the files
   - Auto-generate `manifest.json` if missing (unique UUID + version)
   - Repackage into the correct archive format
4. **Install** – Tap "Install in Minecraft". The system opens Minecraft PE and starts the import automatically.

---

## manifest.json Auto-Generation Logic

If the selected mod has no `manifest.json`, the converter:

1. **Detects pack type** – scans for `textures/`, `behaviors/`, `scripts/` etc.
2. **Generates unique UUIDs** – one for header, one per module
3. **Sets min engine version** to `[1, 20, 0]` (Minecraft 1.20+)
4. **Picks a random creative name** from an internal word bank

If a `manifest.json` already exists but is malformed or incomplete, the app patches only the missing fields.

---

## Android Permissions

| Permission | Reason |
|---|---|
| `READ_EXTERNAL_STORAGE` | Read ZIP/folder from Downloads (Android ≤ 12) |
| `WRITE_EXTERNAL_STORAGE` | Save output `.mcaddon` (Android ≤ 9) |
| `READ_MEDIA_*` | Android 13+ granular media permissions |

On **Android 11–14** the app uses **Storage Access Framework (SAF)** via `ACTION_GET_CONTENT`, so it does NOT need `MANAGE_ALL_FILES`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Minecraft doesn't open after "Install" | Make sure Minecraft PE is installed. Try opening the `.mcaddon` file manually from your file manager. |
| "Conversion failed" | Make sure the ZIP is not password-protected and contains mod files. |
| File picker shows no files | Check that you granted storage permission to the app. |
| Build fails with NDK error | Run `buildozer android clean` then retry. |

---

## Tech Stack

- **Python 3.10+** / **Kivy 2.3** / **KivyMD 1.1**
- **Buildozer** → Android APK
- **pyjnius** → Android Java bridge (Intents, FileProvider, SAF)
- **zipfile** (stdlib) → archive manipulation
- **uuid** (stdlib) → UUID generation
