# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for CodeWidget.

Windows output: dist/CodeWidget.exe   (single-file, windowed, no console)
macOS output:   dist/CodeWidget.app   (app bundle, tray-only, no Dock icon)
Run with:  uv run pyinstaller CodeWidget.spec --clean
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
        (str(ROOT / "config" / "settings.json"), "config"),
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

import sys as _sys

_icns = ROOT / "src" / "assets" / "icon.icns"
_icon = str(_icns if (_sys.platform == "darwin" and _icns.exists()) else ROOT / "src" / "assets" / "icon.ico")

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
    icon=_icon,
)

# macOS: wrap EXE in a .app bundle
if _sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="CodeWidget.app",
        icon=str(_icns) if _icns.exists() else None,
        bundle_identifier="com.sxwins.codewidget",
        info_plist={
            "LSUIElement": True,             # hide from Dock (tray-only app)
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.1.0",
            "CFBundleVersion": "1.1.0",
        },
    )
