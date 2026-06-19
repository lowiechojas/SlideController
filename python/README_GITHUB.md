# ⛪ Church Slide Controller

<div align="center">

<!-- Badges -->
![Python Version](https://img.shields.io/badge/python-3.6%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?logo=windows)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

<!-- Tagline -->
**A lightweight Python web server for remote presentation control over Wi-Fi.**

*Designed for church environments where the pastor needs to control slides from their phone or laptop while the tech booth runs the presentation.*

[Getting Started](#-quick-start) · [Features](#-features) · [Focus Modes](#-focus-modes) · [System Tray](#-system-tray-executable) · [Contributing](#-contributing)

</div>

---

## 📸 Screenshots

> _Screenshots coming soon. Place UI previews here (e.g., mobile web UI, system tray icon, browser login page)._

| Mobile Web UI | Desktop Tray | Login Screen |
|:---:|:---:|:---:|
| `[screenshot]` | `[screenshot]` | `[screenshot]` |

---

## ✨ Features

| | Feature | Description |
|---|---------|-------------|
| 🎮 | **Touch-Friendly Controls** | Large PREV / NEXT buttons optimized for phone screens |
| 🔒 | **Login Authentication** | Session-based cookies with HttpOnly security |
| 🎯 | **3 Focus Modes** | PowerPoint · Custom App · Active Window |
| 📺 | **Smart Window Targeting** | Auto-targets Slide Show window, skips the editor |
| 🌐 | **IP Display in UI** | Server IP shown on screen for easy sharing |
| 💻 | **System Tray Mode** | Windows `.exe` — runs silently in the background |
| 🖥️ | **Cross-Platform** | Windows, macOS, and Linux supported |

---

## 🚀 Quick Start

> **Prerequisites:** Both the tech booth laptop and the pastor's device must be on the **same Wi-Fi network**.

```bash
# Clone the repository
git clone https://github.com/<your-username>/church-slide-controller.git
cd church-slide-controller

# Run the server (no dependencies needed for terminal mode)
python slide_controller.py
```

Then on the pastor's phone or laptop:

1. ✅ Join the same Wi-Fi as the tech booth
2. ✅ Tech booth runs `python slide_controller.py`
3. ✅ Pastor opens `http://<displayed-IP>:8080` in any browser
4. ✅ Login with default credentials → `admin` / `church2025`
5. ✅ Tap **NEXT** or **PREV** to control slides

---

## ⚙️ How It Works

```
Pastor's Phone                 Tech Booth Laptop
─────────────────              ──────────────────────────────
[ Browser UI ]   ──HTTP POST──▶  [ slide_controller.py ]
  NEXT / PREV                       │
                                    ▼
                              Focus Presentation Window
                                    │
                                    ▼
                          Simulate ← → Arrow Keypress
                                    │
                                    ▼
                          [ PowerPoint / Keynote / etc. ]
```

- Server runs on the **same machine** as PowerPoint (or any presentation app)
- Web UI sends `HTTP POST` requests for `next` / `prev` actions
- Server focuses the correct presentation window and simulates arrow keypresses
- Works with **any app** that responds to arrow keys

---

## 🎯 Focus Modes

| Mode | Behavior |
|------|----------|
| **PowerPoint** | Auto-focuses the PowerPoint *Slide Show* window (skips the editor) |
| **Custom App** | Focuses any window matching a user-supplied keyword (case-insensitive substring match) |
| **Active Window** | No focus switch — sends keypress to whatever window is currently in the foreground |

> 💡 **Tip:** Use *Custom App* mode for Keynote, LibreOffice Impress, ProPresenter, or any other presentation software.

---

## 🛠️ Configuration

Edit the constants at the top of `slide_controller.py` to customize behavior:

```python
# ── Server Settings ──────────────────────────────────────────
PORT     = 8080
USERNAME = "admin"
PASSWORD = "church2025"
```

> ⚠️ **Security reminder:** Change the default password before deploying on a shared network.

---

## 💻 System Tray Executable

For a windowless, background experience on **Windows**:

### 1. Install dependencies

```bash
pip install pystray Pillow pyinstaller
```

### 2. Build the `.exe`

```bash
pyinstaller --onefile --noconsole --name SlideController slide_controller_tray.py
```

Or simply run the provided build script:

```bash
build_exe.bat
```

### 3. Tray icon features

- 🖱️ **Hover** the tray icon → see the server IP address
- 🖱️ **Right-click** → open browser, view credentials, or quit

---

## 📋 Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.6 or higher |
| Terminal version | No external packages needed |
| System tray (Windows) | `pystray`, `Pillow` |
| `.exe` build | `pyinstaller` |
| Linux only | `xdotool` |

Install optional dependencies:

```bash
pip install -r requirements.txt
```

---

## 🗂️ Project Structure

```
Church/
├── README.md                        # Top-level overview — Python vs PowerShell
├── docs/
│   ├── SlideController_Documentation.md   # Full technical documentation
│   └── SlideController_Presentation.pptx  # Project presentation slides
├── python/                          ← You are here
│   ├── README.md                    # Python quick-start guide
│   ├── README_GITHUB.md             # GitHub landing page (this file)
│   ├── DISCUSSION_LOG.md            # Development history & design notes
│   ├── slide_controller.py          # Terminal version — all platforms
│   ├── slide_controller_tray.py     # System tray version — Windows
│   ├── build_exe.bat                # One-click .exe build script
│   └── requirements.txt             # Python dependencies
└── powershell/
    ├── README.md                    # PowerShell quick-start guide
    ├── SlideController.ps1          # Zero-install Windows alternative
    ├── Run_SlideController.bat      # Launcher — console mode
    └── Run_SlideController_Tray.bat # Launcher — system tray mode
```

> **Looking for the zero-install Windows version?** See the [`powershell/`](../powershell/) folder — it requires no Python or any other software.

---

## 🔐 Security

- **Session-based authentication** using HttpOnly cookies
- **Random SHA-256 session tokens** generated per login
- **Failed login attempts** are logged with the source IP address

> This tool is intended for use on **trusted local networks** (e.g., church Wi-Fi). It is not hardened for public internet exposure.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](../LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome!

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/my-feature`)
3. **Commit** your changes (`git commit -m 'Add my feature'`)
4. **Push** to the branch (`git push origin feature/my-feature`)
5. **Open a Pull Request**

> For major changes, please **open an issue first** to discuss what you'd like to change.

---

<div align="center">

Made with ❤️ for the local church community

</div>
