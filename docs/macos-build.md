# macOS Build Guide

Step-by-step instructions for building `CodeWidget.app` on macOS.

## Prerequisites

| Tool | Install command |
|------|----------------|
| Homebrew | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Python 3.12 | `brew install python@3.12` |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

Verify:

```bash
python3.12 --version   # Python 3.12.x
uv --version
```

## Step 1 — Clone and install dependencies

```bash
git clone https://github.com/sxwins/CodeWidget.git
cd CodeWidget
uv sync
```

Confirm all tests pass:

```bash
uv run pytest -q    # expected: 38 passed
```

## Step 2 — Create the .icns icon

PyInstaller requires `.icns` format on macOS.
Run this once; the result is committed to the repo after the first time.

```bash
mkdir icon.iconset

sips -z 16   16   src/assets/icon.png --out icon.iconset/icon_16x16.png
sips -z 32   32   src/assets/icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32   32   src/assets/icon.png --out icon.iconset/icon_32x32.png
sips -z 64   64   src/assets/icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128  128  src/assets/icon.png --out icon.iconset/icon_128x128.png
sips -z 256  256  src/assets/icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256  256  src/assets/icon.png --out icon.iconset/icon_256x256.png
sips -z 512  512  src/assets/icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512  512  src/assets/icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 src/assets/icon.png --out icon.iconset/icon_512x512@2x.png

iconutil -c icns icon.iconset -o src/assets/icon.icns
rm -rf icon.iconset
```

## Step 3 — Build

```bash
uv run pyinstaller CodeWidget.spec --clean
```

Output:

```
dist/
├── CodeWidget          ← standalone Unix binary (not used on macOS)
└── CodeWidget.app/     ← macOS app bundle  ✓
```

## Step 4 — Test

```bash
open dist/CodeWidget.app
```

On first launch the app creates a `config/` directory alongside the `.app`:

```
dist/
├── CodeWidget.app
└── config/
    ├── settings.json
    ├── teacher_config.json
    └── school_config.json
```

Open the tray icon → **設定** to configure your courses.

## Step 5 — Gatekeeper (first run on another Mac)

Because the app is not notarized, macOS will block it on first launch.
To open it anyway:

```
Right-click CodeWidget.app → Open → Open  (in the warning dialog)
```

This only needs to be done once per machine.

Alternatively, remove the quarantine flag:

```bash
xattr -dr com.apple.quarantine dist/CodeWidget.app
```

## Optional — Ad-hoc code signing

Removes the Gatekeeper warning for colleagues on the same local network
without requiring an Apple Developer account:

```bash
codesign --deep --force --sign - dist/CodeWidget.app
```

## Optional — Create a DMG for distribution

```bash
brew install create-dmg

create-dmg \
  --volname "CodeWidget" \
  --window-size 600 400 \
  --icon-size 128 \
  --icon "CodeWidget.app" 150 185 \
  --app-drop-link 450 185 \
  "dist/CodeWidget-1.0.0.dmg" \
  "dist/CodeWidget.app"
```

## Differences from Windows build

| | Windows | macOS |
|---|---|---|
| Output | `CodeWidget.exe` | `CodeWidget.app` |
| Icon format | `.ico` | `.icns` |
| Spec addition | — | `BUNDLE` block |
| Tray-only (no Dock) | automatic | `LSUIElement: True` in `info_plist` |
| Config location | next to `.exe` | next to `.app` (handled by `_user_data_dir`) |
| Code signing | — | optional ad-hoc or Apple Developer |
