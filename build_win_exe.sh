#!/usr/bin/env bash
set -euo pipefail

# Build script (Linux / macOS) that runs PyInstaller.
# NOTE: PyInstaller builds a native executable for the current OS. To build a Windows
# .exe you should run this on Windows (or use Wine / cross-compilation tools).

# Simple one-file build (console will be shown):
pyinstaller --clean --noconfirm --onefile --name Win --console Win.py

# If the above misses pygame assets, try using the included spec:
# pyinstaller --clean --noconfirm win.spec

echo "Build finished. Check the 'dist' folder for the built binary (dist/Win or dist/Win.exe)."