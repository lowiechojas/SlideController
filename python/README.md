# Church Slide Controller

## Overview
A lightweight Python web server that runs on the tech booth laptop. It provides a mobile-friendly UI with Next/Prev buttons to control a presentation slideshow. The pastor (or anyone on the same network) opens the URL in a browser to advance or go back slides.

## Setup
1. Both laptops connect to the same Wi-Fi network
2. Tech booth laptop launches the presentation app (PowerPoint, Google Slides, LibreOffice Impress, etc.)
3. Tech booth laptop runs the server script
4. Pastor opens the displayed URL on their phone/laptop browser

## Usage
```bash
python slide_controller.py
```

The script prints the URL to open (e.g., `http://192.168.1.x:8080`). The same IP is also shown in the web UI for easy sharing.

## Features

### Server IP in UI
The server's IP address and port are displayed at the top of the web page so the pastor can easily type it in.

### Focus Mode (3 options)
1. **PowerPoint** — always focuses the PowerPoint window before sending keypress
2. **Custom App** — type any keyword from the target window's title (case-insensitive substring match). Examples:
   - "Word" matches "Microsoft Word - Document1.docx"
   - "Chrome" matches "Google Chrome"
   - "Impress" matches "LibreOffice Impress"
3. **Active Window** — no focus switch; sends the keypress to whatever window is currently in the foreground

### Other
- **Auto-focus** — for modes 1 & 2, brings the target app to the foreground before sending the keypress, even if other apps are open
- **Instructions in UI** — step-by-step guide shown directly on the page
- **Cross-platform** — Windows, macOS, Linux

## Requirements
- Python 3 (no external packages needed on Windows)
- On Linux: install `xdotool` (`sudo apt install xdotool`)
- On macOS: allow Accessibility permissions for Terminal

## How It Works
- The web UI sends POST requests to `/api/slide` with `{"action": "next"}` or `{"action": "prev"}`
- Based on the focus mode, the server optionally focuses the target app window
- Then it simulates Right/Left arrow keypresses
- The presentation app responds and changes slides

## API
- `GET /` — Main web UI (shows IP, controls, instructions)
- `POST /api/slide` — `{"action": "next"}` or `{"action": "prev"}`
- `POST /api/target` — `{"app": "PowerPoint"}` or `{"app": "__active__"}` — change focus mode

## Building as Windows Executable (System Tray App)

A separate `slide_controller_tray.py` version runs as a system tray icon in the lower-right corner of Windows.

### To build:
1. Open a terminal in this folder on Windows
2. Run `build_exe.bat` (installs dependencies and builds the `.exe`)
3. The executable will be in `dist\SlideController.exe`

### System tray features:
- Hover over the tray icon to see the server IP and port
- Right-click for menu: open in browser, see credentials, or quit
- No terminal window — runs silently in the background

### Dependencies (auto-installed by build script):
- `pystray` — system tray integration
- `Pillow` — icon generation
- `pyinstaller` — packages into a single `.exe`

## Platform Support
- Windows (uses `ctypes` — no install needed)
- macOS (uses `osascript`)
- Linux (uses `xdotool`)
