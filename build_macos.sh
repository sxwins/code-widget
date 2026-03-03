#!/usr/bin/env bash
# build_macos.sh — macOS 用ビルドスクリプト
# 使用法: ./build_macos.sh
# 必須: macOS + sips + iconutil (Xcode Command Line Tools)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
PNG="$ROOT/src/assets/icon.png"
ICNS="$ROOT/src/assets/icon.icns"
ICONSET="$ROOT/icon.iconset"

echo "==> Generating icon.icns from icon.png ..."
rm -rf "$ICONSET"
mkdir "$ICONSET"
sips -z 16   16   "$PNG" --out "$ICONSET/icon_16x16.png"    > /dev/null
sips -z 32   32   "$PNG" --out "$ICONSET/icon_16x16@2x.png" > /dev/null
sips -z 32   32   "$PNG" --out "$ICONSET/icon_32x32.png"    > /dev/null
sips -z 64   64   "$PNG" --out "$ICONSET/icon_32x32@2x.png" > /dev/null
sips -z 128  128  "$PNG" --out "$ICONSET/icon_128x128.png"  > /dev/null
sips -z 256  256  "$PNG" --out "$ICONSET/icon_128x128@2x.png" > /dev/null
sips -z 256  256  "$PNG" --out "$ICONSET/icon_256x256.png"  > /dev/null
sips -z 512  512  "$PNG" --out "$ICONSET/icon_256x256@2x.png" > /dev/null
sips -z 512  512  "$PNG" --out "$ICONSET/icon_512x512.png"  > /dev/null
sips -z 1024 1024 "$PNG" --out "$ICONSET/icon_512x512@2x.png" > /dev/null
iconutil -c icns "$ICONSET" -o "$ICNS"
rm -rf "$ICONSET"
echo "    -> $ICNS"

echo "==> Building CodeWidget.app ..."
uv run pyinstaller CodeWidget.spec --clean

echo ""
echo "Done! -> dist/CodeWidget.app"
