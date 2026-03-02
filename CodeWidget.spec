# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for CodeWidget.

Output: dist/CodeWidget.exe  (single-file, windowed, no console)
Run with:  uv run pyinstaller CodeWidget.spec
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "src" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        # Bundle the app icon
        (str(ROOT / "src" / "assets" / "icon.png"), "assets"),
        # Bundle the default config templates (seeded to config/ on first run)
        (str(ROOT / "config" / "school_config.json"), "config"),
        (str(ROOT / "config" / "teacher_config.json"), "config"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CodeWidget",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "src" / "assets" / "icon.ico"),
)
