# Church Slide Controller — Technical Documentation

**Version:** 2.0  
**Date:** June 2025  
**Author:** Lowie Hojas

---

## 1. Introduction

### 1.1 Purpose
This document provides complete technical documentation for the Church Slide Controller software — a lightweight web server for remote presentation control over a local Wi-Fi network. The project ships in **two implementations**: a **Python** version (cross-platform) and a **PowerShell** version (Windows, zero-install).

### 1.2 Problem Statement
In church settings, HDMI connectivity issues between the pastor's laptop and the projector create disruptions during worship services. The tech booth laptop has a reliable HDMI connection to the projector, but the pastor needs the ability to advance slides at their own pace.

### 1.3 Solution
A web server runs on the tech booth laptop alongside the presentation software. The pastor accesses a mobile-friendly web interface from any device on the same network to control slides remotely. Two versions are available to accommodate different environments and operator skill levels.

### 1.4 Choosing a Version

| Criterion | Python Version | PowerShell Version |
|-----------|---------------|-------------------|
| **Installation required** | Python 3.6+ (usually pre-installed) | None — built into Windows |
| **Operating systems** | Windows, macOS, Linux | Windows only |
| **Standalone .exe** | Yes, via PyInstaller | N/A |
| **Best for** | Cross-platform or Linux/macOS setups | Windows PCs where no software can be installed |

---

## 2. System Architecture

### 2.1 Overview
- **Server**: Tech booth laptop (runs presentation + slide controller server)
- **Client**: Pastor's phone/laptop/tablet (browser-based UI)
- **Communication**: HTTP over local Wi-Fi (port 8080)
- **Control Method**: Simulated keyboard arrow key presses

### 2.2 Data Flow
1. Pastor taps NEXT/PREV on web UI
2. Browser sends HTTP POST to /api/slide
3. Server validates session cookie
4. Server focuses target application window
5. Server simulates Right/Left arrow keypress
6. Presentation software advances/reverses slide

---

## 3. Features

Both implementations share the same feature set:

### 3.1 Authentication
- Session-based login with HttpOnly cookies
- SHA-256 random session tokens (Python) / GUID tokens (PowerShell)
- Default credentials: admin / church2025
- Failed login attempts logged with client IP
- Sessions persist until server restart

### 3.2 Focus Modes
Three focus modes determine how the server targets the application:

| Mode | Description | Use Case |
|------|-------------|----------|
| PowerPoint | Focuses window with "PowerPoint" AND "Slide Show" in title; falls back to any PowerPoint window | Default for church use |
| Custom App | Focuses any window whose title contains the user-specified keyword (case-insensitive) | Google Slides in Chrome, LibreOffice Impress, etc. |
| Active Window | Skips focus; sends keypress to whatever is in foreground | When operator manually manages focus |

### 3.3 PowerPoint Slide Show Priority
When in PowerPoint mode, the software prioritizes the Slide Show window over the editor window. This ensures that during a presentation, the keypress goes directly to the active slideshow without needing to click twice.

### 3.4 Web UI Features
- Large touch-friendly buttons (140×140 px)
- Server IP displayed prominently for easy sharing
- Inline usage instructions
- Real-time status feedback ("NEXT sent", "PREV sent")
- Keyboard support (arrow keys when browser is focused)
- Responsive design for mobile devices

### 3.5 System Tray Mode (Windows)
- Runs as a background application with icon in Windows notification area
- Hover tooltip shows server URL
- Right-click context menu: URL, credentials, open browser, quit
- No visible terminal window
- **Python version**: Packaged as single `.exe` via PyInstaller
- **PowerShell version**: Launched via `Run_SlideController_Tray.bat`

---

## 4. Installation & Setup

### 4.1 Python Version

#### Requirements
- Python 3.6 or higher
- No external packages for terminal version
- For system tray version: `pystray`, `Pillow`
- For building `.exe`: `pyinstaller`
- For Linux: `xdotool` package

#### Terminal Version
```bash
cd python/
python slide_controller.py
```

#### System Tray Version
```bash
cd python/
pip install pystray Pillow
python slide_controller_tray.py
```

#### Building Windows Executable
```bash
cd python/
pip install pystray Pillow pyinstaller
pyinstaller --onefile --noconsole --name SlideController slide_controller_tray.py
```
Output: `python/dist/SlideController.exe`

---

### 4.2 PowerShell Version

#### Requirements
- Windows 7 or later (PowerShell is built-in — no installation needed)

#### Console Mode
Double-click `powershell/Run_SlideController.bat`

#### System Tray Mode (hidden window, icon in taskbar)
Double-click `powershell/Run_SlideController_Tray.bat`

#### First-Run Permission (one-time, if needed)
If you see a "Could not start listener" error, run the following **once** as Administrator:
```powershell
netsh http add urlacl url=http://+:8080/ user=%USERNAME%
```
After that, the script runs normally without administrator rights.

#### Implementation Notes
- Uses `.NET HttpListener` for the HTTP server
- Uses `WScript.Shell` for simulating arrow keypresses
- Uses `WinForms` for the system tray icon
- Credential and port settings are editable at the top of `SlideController.ps1`

---

## 5. Usage

### 5.1 Step-by-Step (Both Versions)
1. Connect both the tech booth laptop and pastor's device to the same Wi-Fi network
2. Open the presentation in PowerPoint (or other software) on the tech booth laptop
3. Start the slide controller server (Python or PowerShell — your choice)
4. Note the IP address displayed in the terminal, console, or system tray tooltip
5. On the pastor's device, open a browser and navigate to `http://<IP>:8080`
6. Login with credentials (default: admin / church2025)
7. Select the appropriate Focus Mode
8. Start the slideshow on the tech booth
9. Use PREV/NEXT buttons to control slides

### 5.2 Configuration — Python Version
Edit the following constants at the top of `slide_controller.py`:
```python
PORT = 8080                 # Server port
TARGET_APP = "PowerPoint"   # Default target application
USERNAME = "admin"          # Login username
PASSWORD = "church2025"     # Login password
```

### 5.3 Configuration — PowerShell Version
Edit the following variables at the top of `SlideController.ps1`:
```powershell
$port     = 8080
$username = "admin"
$password = "church2025"
```

---

## 6. API Reference

Both versions expose an identical HTTP API:

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/` | GET | — | Serves login page or main UI |
| `/api/login` | POST | `{"username": "...", "password": "..."}` | Authenticate and receive session cookie |
| `/api/slide` | POST | `{"action": "next"}` or `{"action": "prev"}` | Advance or reverse slide |
| `/api/target` | POST | `{"app": "PowerPoint"}` or `{"app": "__active__"}` | Change focus mode/target |

---

## 7. Security Considerations

- Credentials are stored in plaintext in the script (suitable for local church network use)
- No HTTPS (communication is over local network only)
- Session tokens are cryptographically random (Python: `os.urandom` + SHA-256; PowerShell: `[System.Guid]::NewGuid()`)
- HttpOnly cookies prevent XSS token theft
- Designed for trusted local networks, not public internet

---

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| Keypress targets wrong window | Change Focus Mode or ensure presentation is in Slide Show mode |
| Can't connect from pastor's device | Verify both devices are on same Wi-Fi; check firewall allows port 8080 |
| "python" not recognized | Use `python3` or `py` instead |
| Slideshow requires double-click | Fixed in current version — Slide Show window is prioritized |
| PowerShell: "Could not start listener" | Run `netsh http add urlacl url=http://+:8080/ user=%USERNAME%` once as Administrator |
| PowerShell script won't run | Execution policy may be restricted; the `.bat` launchers bypass this automatically |

---

## 9. File Structure

```
Church/
├── README.md                        # Top-level overview — choose Python or PowerShell
├── docs/
│   ├── SlideController_Documentation.md   # This file
│   └── SlideController_Presentation.pptx  # Project presentation slides
├── python/
│   ├── README.md                    # Python version quick reference
│   ├── README_GITHUB.md             # GitHub landing page
│   ├── DISCUSSION_LOG.md            # Development history
│   ├── slide_controller.py          # Terminal version (cross-platform)
│   ├── slide_controller_tray.py     # System tray version (Windows)
│   ├── build_exe.bat                # One-click .exe build script
│   └── requirements.txt             # Python dependencies
└── powershell/
    ├── README.md                    # PowerShell version quick reference
    ├── SlideController.ps1          # Main PowerShell script
    ├── Run_SlideController.bat      # Launcher — console mode
    └── Run_SlideController_Tray.bat # Launcher — system tray mode
```

---

**End of Document**
