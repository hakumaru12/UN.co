@echo off
REM Build script for Windows using PyInstaller
REM Requires Python + PyInstaller installed in the environment






pyinstaller --clean --noconfirm --onefile --name Win --console Win.py

REM Upgrade pip
python -m pip install --upgrade pip

REM Create a Windows-specific requirements file excluding Linux-only packages (e.g., RPi.GPIO)
if exist req.txt (
    powershell -NoProfile -Command "Get-Content 'req.txt' | Where-Object { $_ -and -not ($_ -match 'sys_platform\s*==\s\"linux\"') } | Set-Content 'req-windows.txt'"
    python -m pip install -r req-windows.txt
    if exist req-windows.txt del /f /q req-windows.txt
) else (
    python -m pip install pyinstaller pygame
)

REM Build console exe (shows console)
pyinstaller --clean --noconfirm --onefile --name Win --console Win.py

IF EXIST dist\Win.exe (
    echo Build succeeded: dist\Win.exe
) ELSE (
    echo dist\Win.exe not found, trying spec-based build...
    pyinstaller --clean --noconfirm win.spec
    IF EXIST dist\Win.exe (
        echo Build succeeded: dist\Win.exe
    ) ELSE IF EXIST dist\Win\Win.exe (
        echo Build succeeded: dist\Win\Win.exe
    ) ELSE (
        echo Build failed. See PyInstaller output above.
        exit /b 1
    )
)

echo Build finished. Check the dist\ folder for the built binary.