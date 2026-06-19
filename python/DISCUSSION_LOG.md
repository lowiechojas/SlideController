# Church Slide Controller — Discussion Log

## Concept
- Problem: HDMI connection issues between pastor's laptop and projector
- Solution: A mini web server running on the tech booth laptop that serves a UI with Next/Prev buttons to control slides remotely
- The pastor connects to the same network and controls slides from their phone/laptop browser

## Architecture
- **Tech booth laptop**: Runs PowerPoint + the Python server script
- **Pastor's laptop/phone**: Opens the web UI to control slides
- Both tech booth and pastor can control simultaneously

## Features Implemented

### 1. Core Slide Control
- Web UI with large touch-friendly PREV/NEXT buttons
- Simulates keyboard arrow keys (Right/Left) to control slides
- Cross-platform support (Windows, macOS, Linux)

### 2. Server IP Displayed in UI
- IP address shown at the top of the web page for easy sharing with the pastor
- Instructions embedded directly in the UI

### 3. Dynamic Focus Mode (3 options)
1. **PowerPoint** — always focuses the PowerPoint window (prioritizes Slide Show window over editor)
2. **Custom App** — user types any keyword from the target window title (case-insensitive substring match)
3. **Active Window** — no focus switch; sends keypress to whatever is currently in foreground

### 4. Login Authentication
- Session-based authentication with cookie
- Login page required before accessing controls
- Default credentials: admin / church2025
- Failed login attempts logged in terminal

### 5. PowerPoint Slide Show Priority
- When PowerPoint is presenting, the controller targets the Slide Show window directly (not the editor)
- Falls back to editor window if not in presentation mode

### 6. System Tray Executable
- `slide_controller_tray.py` — runs as a Windows system tray icon
- Hover to see IP address
- Right-click menu: URL, credentials, open browser, quit
- `build_exe.bat` packages it into a single `.exe` using PyInstaller
- No terminal window visible

## Files
- `slide_controller.py` — Terminal version (run with `python slide_controller.py`)
- `slide_controller_tray.py` — System tray version for Windows
- `build_exe.bat` — Build script to create `.exe`
- `requirements.txt` — Python dependencies (pystray, Pillow, pyinstaller)
- `README.md` — Full documentation

## Technical Notes
- Window matching uses case-insensitive substring search on window titles
- "Word" matches "Microsoft Word - Document1.docx"
- "Chrome" matches "Google Chrome"
- Sessions are in-memory (reset when server restarts)
- Server runs on port 8080 by default

---

## PowerShell Version Added

A second implementation of the slide controller was created in PowerShell as a **zero-installation alternative for Windows**.

### Motivation
The Python version works well, but it requires Python to be installed on the tech booth laptop. In some church environments, tech booth PCs are locked down or managed — installing software may not be allowed or practical. PowerShell is built into every Windows machine (Windows 7+), so no installation step is needed at all.

### What Was Built
- `powershell/SlideController.ps1` — a single script that replicates all functionality of the Python version
- `powershell/Run_SlideController.bat` — double-click launcher for console mode
- `powershell/Run_SlideController_Tray.bat` — double-click launcher for system tray mode (hidden window)

### Implementation Approach
| Concern | Python approach | PowerShell approach |
|---------|----------------|---------------------|
| HTTP server | `http.server` (stdlib) | `.NET HttpListener` |
| Keypresses | `ctypes` / `osascript` / `xdotool` | `WScript.Shell` |
| System tray | `pystray` + `Pillow` | `WinForms` (built-in .NET) |
| Session tokens | `os.urandom` + SHA-256 | `[System.Guid]::NewGuid()` |

### Feature Parity
The PowerShell version is fully feature-equivalent to the Python version:
- Login authentication (session-based, HttpOnly cookies)
- 3 Focus Modes: PowerPoint, Custom App, Active Window
- PowerPoint Slide Show window priority
- Server IP displayed in the web UI
- System tray mode with hover tooltip and right-click menu
- Default credentials: admin / church2025 on port 8080

### Known Constraint
On some Windows systems, binding to `http://+:8080/` requires a one-time admin command:
```
netsh http add urlacl url=http://+:8080/ user=%USERNAME%
```
After this is run once, the script works normally without administrator privileges.
