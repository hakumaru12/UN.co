# PowerShell helper to build Win.exe locally on Windows
set -e

Write-Host "Checking Python and PyInstaller..."
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python not found in PATH. Install Python first."
    exit 1
}

python -m pip install --upgrade pip

# On Windows, skip Linux-only packages (like RPi.GPIO) when installing requirements
if (Test-Path req.txt) {
    Write-Host "Filtering req.txt for this platform..."
    $filtered = Get-Content req.txt | Where-Object { $_ -and -not ($_.Trim() -like "*sys_platform ==*\"linux\"") }
    $tmp = "$PWD\req-windows.txt"
    $filtered | Set-Content -Path $tmp -Encoding UTF8
    python -m pip install -r $tmp
    Remove-Item $tmp -ErrorAction SilentlyContinue
} else {
    python -m pip install pyinstaller pygame
}

# Build Win_gui if present
if (Test-Path .\Win_gui.py) {
    Write-Host "Building Win_gui (GUI) EXE..."
    pyinstaller --noconfirm --onefile --windowed --name SteerRC Win_gui.py
} else {
    Write-Host "Win_gui.py not found; skipping GUI build."
}

Write-Host "Building Win.exe with PyInstaller (onefile, console)..."
pyinstaller --clean --noconfirm --onefile --name Win --console Win.py

if (Test-Path .\dist\Win.exe) {
    Write-Host "Build succeeded: .\dist\Win.exe"
    exit 0
}

Write-Host "dist\Win.exe not found, trying spec-based build..."
pyinstaller --clean --noconfirm win.spec

if (Test-Path .\dist\Win.exe -or Test-Path .\dist\Win\Win.exe) {
    Write-Host "Build succeeded. Check .\dist for the exe."
    exit 0
}

Write-Error "Build failed. Check PyInstaller output above for errors."
exit 1