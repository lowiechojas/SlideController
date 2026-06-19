# Church Slide Controller — PowerShell Version

## Overview
Same functionality as the Python version, but runs natively on any Windows PC with **zero installation required**. PowerShell is built into every Windows machine.

## Files
- `SlideController.ps1` — Main PowerShell script
- `Run_SlideController.bat` — Double-click to run in console mode
- `Run_SlideController_Tray.bat` — Double-click to run in system tray mode (hidden window)

## Usage

### Console Mode (with terminal output)
Double-click `Run_SlideController.bat`

### System Tray Mode (hidden, icon in taskbar)
Double-click `Run_SlideController_Tray.bat`

## First Run Note
If you get a "Could not start listener" error, run this **once** as Administrator:
```powershell
netsh http add urlacl url=http://+:8080/ user=%USERNAME%
```
Then run the script again normally.

## Features
- Login authentication
- 3 Focus Modes (PowerPoint, Custom App, Active Window)
- Slide Show window priority
- Server IP in UI
- System tray with hover tooltip showing IP
- No Python or any other software required

## Default Credentials
- Username: `admin`
- Password: `church2025`

Edit the top of `SlideController.ps1` to change.
