# Windows helper script to build standalone exe with PyInstaller
python -m pip install --upgrade pip
python -m pip install -r req.txt
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name SteerRC Win_gui.py
if (Test-Path .\dist\SteerRC.exe) {
    Write-Host "Build succeeded: dist\SteerRC.exe"
} else {
    Write-Host "Build failed. See PyInstaller output above."
    exit 1
}