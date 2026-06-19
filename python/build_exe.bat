@echo off
echo Installing dependencies...
py -m pip install pystray Pillow pyinstaller

echo.
echo Building executable...
py -m PyInstaller --onefile --noconsole --name SlideController slide_controller_tray.py

echo.
echo Done! Executable is in: dist\SlideController.exe
pause
