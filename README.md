# 🍎 macOS Version — Slide Controller

**Menu bar app for macOS** — runs in the status bar, controlled from the pastor's phone.

---

## 🚀 Quick Start

### Terminal Mode (no dependencies)
```bash
python3 slide_controller_mac.py
```
This works immediately with **zero pip installs**. The server runs in the terminal and uses `osascript` for keystroke simulation.

### Menu Bar Mode (recommended)
```bash
pip3 install rumps
python3 slide_controller_mac.py
```
Adds a ⛪ icon to your macOS menu bar with quick access to the URL and credentials.

---

## 📦 Build Standalone .app

```bash
./build_app.sh
```
Creates `dist/SlideController.app` — double-click to run, no Python needed.

---

## ⚠️ macOS Permissions

On first run, macOS will prompt you to grant **Accessibility** access:

1. Go to **System Settings → Privacy & Security → Accessibility**
2. Add **Terminal** (or **SlideController.app** if using the built app)
3. Toggle it ON

This is required for `System Events` to send keystrokes to other apps.

---

## 🎯 Supported Presentation Apps

- **Keynote** — set Focus Mode to "Custom App" and type `Keynote`
- **PowerPoint** — default setting
- **Google Slides** (in browser) — set to "Active Window" mode
- **LibreOffice Impress** — set Custom App to `Impress`

---

## 📋 Default Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `church2025` |
| Port | `8080` |

Change these at the top of `slide_controller_mac.py` before deploying.
