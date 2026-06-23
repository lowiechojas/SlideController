#!/bin/bash
# Build a standalone .app bundle for macOS
pip3 install rumps pyinstaller
pyinstaller --onefile --windowed \
    --name "SlideController" \
    --osx-bundle-identifier "com.church.slidecontroller" \
    slide_controller_mac.py
echo ""
echo "Done! App bundle is in dist/SlideController.app"
