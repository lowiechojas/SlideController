# ⛪ Church Slide Controller

**Remote presentation control over Wi-Fi — runs on the tech booth laptop, controlled from the pastor's phone.**

This project has **two implementations** that deliver identical functionality. Choose the one that best fits your setup:

---

## 🤔 Which Version Should I Use?

| | [🐍 Python Version](python/) | [⚡ PowerShell Version](powershell/) |
|---|---|---|
| **Installation** | Python 3.6+ required | **Zero install** — built into Windows |
| **Platforms** | Windows, macOS, Linux | Windows only |
| **Standalone .exe** | ✅ Yes, via PyInstaller | ❌ N/A |
| **System tray** | ✅ Yes | ✅ Yes |
| **Best for** | Cross-platform setups; macOS/Linux; advanced users | Any Windows PC, especially when software installs are restricted |

> **Short answer:**  
> - On **Windows** and want the simplest possible setup → use **PowerShell**  
> - On **macOS**, **Linux**, or want a `.exe` → use **Python**

---

## ✨ Features (Both Versions)

| | Feature | Description |
|---|---------|-------------|
| 🔒 | **Login Authentication** | Session-based cookies with HttpOnly security |
| 🎯 | **3 Focus Modes** | PowerPoint · Custom App · Active Window |
| 📺 | **Slide Show Priority** | Auto-targets the Slide Show window, not the editor |
| 🌐 | **IP Displayed in UI** | Server IP shown on screen — easy to share with the pastor |
| 🖥️ | **System Tray Mode** | Runs silently in the background, icon in notification area |
| 🎮 | **Touch-Friendly Controls** | Large PREV / NEXT buttons optimized for phone screens |

**Default credentials:** `admin` / `church2025` — change at the top of either script before deploying.  
**Port:** `8080`

---

## 🚀 Quick Start

### Python Version
```bash
cd python/
python slide_controller.py
```
See [`python/README.md`](python/README.md) for tray mode, `.exe` build instructions, and platform requirements.

### PowerShell Version
Double-click **`powershell/Run_SlideController.bat`** (console) or **`powershell/Run_SlideController_Tray.bat`** (system tray).

> ⚠️ First run only: if you see a "Could not start listener" error, run once as Administrator:
> ```powershell
> netsh http add urlacl url=http://+:8080/ user=%USERNAME%
> ```

See [`powershell/README.md`](powershell/README.md) for details.

---

## 🗂️ Project Structure

```
Church/
├── README.md                        ← You are here
├── docs/
│   ├── SlideController_Documentation.md   # Full technical documentation
│   └── SlideController_Presentation.pptx  # Project presentation slides
├── python/
│   ├── README.md                    # Python quick-start guide
│   ├── README_GITHUB.md             # GitHub landing page
│   ├── DISCUSSION_LOG.md            # Development history & design notes
│   ├── slide_controller.py          # Terminal version (cross-platform)
│   ├── slide_controller_tray.py     # System tray version (Windows)
│   ├── build_exe.bat                # One-click .exe build script
│   └── requirements.txt             # Python dependencies
└── powershell/
    ├── README.md                    # PowerShell quick-start guide
    ├── SlideController.ps1          # Main script (zero-install on Windows)
    ├── Run_SlideController.bat      # Launcher — console mode
    └── Run_SlideController_Tray.bat # Launcher — system tray mode
```

---

## ⚙️ How It Works

```
Pastor's Phone / Tablet          Tech Booth Laptop
──────────────────────           ──────────────────────────────
[ Browser UI ]   ──HTTP POST──▶  [ Slide Controller Server ]
  NEXT / PREV                          │
                                       ▼
                               Focus Presentation Window
                                       │
                                       ▼
                           Simulate ← → Arrow Keypress
                                       │
                                       ▼
                           [ PowerPoint / Keynote / Impress ]
```

Both the pastor and the tech booth operator can control slides simultaneously. Works with any presentation app that responds to arrow keys.

---

## 📄 Documentation

Full technical documentation — architecture, API reference, security notes, and troubleshooting — is in [`docs/SlideController_Documentation.md`](docs/SlideController_Documentation.md).

---

<div align="center">

Made with ❤️ for the local church community

</div>
