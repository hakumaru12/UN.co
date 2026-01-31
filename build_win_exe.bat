@echo off
REM Build script for Windows using PyInstaller
REM Requires Python + PyInstaller installed in the environment






pyinstaller --clean --noconfirm --onefile --name Win --console Win.py

echo Build finished. Check the dist\Win.exe file.
REM If you run into missing pygame assets, run the spec-based build:
REM pyinstaller --clean --noconfirm win.spec