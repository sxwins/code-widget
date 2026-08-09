# CodeWidget v1.1 — Release Notes

**Release date:** 2026-08-08

---

## Downloads

| Platform | File |
|----------|------|
| Windows 10 / 11 | `CodeWidget.exe` |
| macOS (Apple Silicon) | `CodeWidget-v1.1-mac-arm64.zip` → unzip → run `CodeWidget.app` |

---

## Bug Fixes

### Attendance code not refreshing after config save (critical)

When editing an attendance code inside an active class window and saving,
the displayed code was not updated until the application was restarted.

Root cause: `_build_all_scheduled()` reassigns session keys after each save,
causing the lookup to target the wrong session. The fix pushes the UI update
via the existing `_last_active` reference before the session key re-ordering
takes effect.

### Skip / makeup override corrupted on edit

Editing a `skip` or `makeup` override through the dialog silently converted
it to a `reschedule` record, causing incorrect schedule behavior.
The fix preserves the original override type on save.

### Application crash on malformed config dates

Unprotected `date.fromisoformat()` calls caused an unhandled `ValueError` and
silent crash when config files contained non-ISO date strings (e.g. `2026/04/01`).
All date parsing is now wrapped with error handling; malformed records are
skipped with a warning rather than crashing the app.

### Temp code not reverting after TTL expiry

A temporary attendance code that expired mid-class would remain displayed
until the next state change (e.g. class end). The ticker now detects temp code
expiry independently of session changes and reverts to the regular code immediately.

### Window restored off-screen on multi-monitor setups

On launch, if the saved window position was outside all connected screens
(e.g. after disconnecting a monitor), the window was invisible and could not
be moved. The app now detects this condition and resets the window to the
primary screen.

### Tray menu label out of sync

The "Show / Hide window" tray menu item showed the wrong label depending on
window state. It now reflects the actual visibility at the time the menu opens.

---

## Improvements

### macOS support

- Added `CodeWidget.app` bundle output via PyInstaller spec
- Added `icon.icns` (7 sizes: 16–1024 px) for correct macOS app icon display
- App runs as a menu bar–only application (no Dock icon) via `LSUIElement`

### Open-source release

- Added MIT `LICENSE`
- Added `NOTICE` with PySide6 LGPL v3 attribution
- Published source at: https://github.com/sxwins/code-widget

### Documentation

- Bilingual README in English and Japanese
- User manuals updated with actual screenshots (v1.1)

---

## Known Issues

| ID | Description |
|----|-------------|
| TD-01 | `Appearance` class defined in `teacher_config.py` instead of `app_settings.py` — low impact, cosmetic only |
| TD-02 | Multiple custom-start sessions on the same day sorted by `(date, period)` only; order may differ from actual start times — extremely rare scenario |
