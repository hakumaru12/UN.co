# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for building `Win.py` as an executable.
This spec collects pygame submodules and data files so the resulting binary behaves like running `python Win.py`.

Usage:
  pyinstaller win.spec

If you prefer a single-file build use the provided build scripts which call PyInstaller with --onefile.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('pygame')
datas = collect_data_files('pygame')

block_cipher = None

a = Analysis(
    ['Win.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Win',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Ensure console is shown when the exe runs
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Win',
)
