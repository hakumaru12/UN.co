# Windows helper script to build standalone exe with PyInstaller
python -m pip install --upgrade pip

# Filter out Linux-only requirements (e.g., RPi.GPIO) on Windows
if (Test-Path req.txt) {
    Write-Host "Filtering req.txt for Windows..."
    # Use regex match to avoid nested-quote parsing issues
    $filtered = Get-Content req.txt | Where-Object { $_ -and -not ($_.Trim() -match 'sys_platform\s*==\s"linux"') }
    $tmp = "$PWD\req-windows.txt"
    $filtered | Set-Content -Path $tmp -Encoding UTF8
    python -m pip install -r $tmp
    Remove-Item $tmp -ErrorAction SilentlyContinue
} else {
    python -m pip install pyinstaller pygame
}

# Build GUI exe if source exists
if (Test-Path .\Win_gui.py) {
    Write-Host "Building SteerRC (GUI) EXE..."
    pyinstaller --noconfirm --onefile --windowed --name SteerRC Win_gui.py
    if (Test-Path .\dist\SteerRC.exe) {
        Write-Host "Build succeeded: dist\SteerRC.exe"
    } else {
        Write-Host "SteerRC build failed. See PyInstaller output above."
    }
} else {
    Write-Host "Win_gui.py not found; skipping GUI build."
}

# Build console Win exe
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