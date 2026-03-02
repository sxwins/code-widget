"""app_settings.py — global application settings: active teacher config path + appearance.

File layout (settings.json):
  active_config   — absolute path to the current teacher config JSON;
                    empty string = use DEFAULT_TEACHER_CONFIG
  appearance{}    — all display settings (font, color, window scale)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from models.teacher_config import Appearance


@dataclass
class AppSettings:
    active_config: str = ""  # absolute path; empty = DEFAULT_TEACHER_CONFIG
    appearance: Appearance = field(default_factory=Appearance)


def load_app_settings(path: str | Path) -> AppSettings:
    """Load settings.json; return defaults if the file doesn't exist."""
    p = Path(path)
    if not p.exists():
        return AppSettings()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    return AppSettings(
        active_config=data.get("active_config", ""),
        appearance=Appearance(**{
            k: v for k, v in data.get("appearance", {}).items()
            if k in Appearance.__dataclass_fields__
        }),
    )


def save_app_settings(settings: AppSettings, path: str | Path) -> None:
    """Serialise AppSettings to settings.json."""
    data = {
        "active_config": settings.active_config,
        "appearance": {
            "code_font_family": settings.appearance.code_font_family,
            "code_font_size": settings.appearance.code_font_size,
            "code_color": settings.appearance.code_color,
            "code_bg_color": settings.appearance.code_bg_color,
            "border_color": settings.appearance.border_color,
            "course_font_family": settings.appearance.course_font_family,
            "course_font_size": settings.appearance.course_font_size,
            "window_scale": settings.appearance.window_scale,
        },
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
