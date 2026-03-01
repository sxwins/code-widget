from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Slot:
    weekday: str  # "Monday" / "Tuesday" / ...
    period: int   # 1~6


@dataclass
class Course:
    id: str
    name: str
    course_type: str   # "spring","autumn","Q1"~"Q4","intensive"
    slots: list[Slot]
    course_code: str = ""


@dataclass
class Override:
    type: str          # "skip" | "makeup" | "reschedule"
    course_id: str
    # skip / makeup
    date: str = ""
    period: int | None = None
    # reschedule
    original_date: str = ""
    original_period: int | None = None
    new_date: str = ""
    new_period: int | None = None
    new_start_time: str = ""


@dataclass
class WindowPosition:
    x: int = 100
    y: int = 100


@dataclass
class Settings:
    pre_class_minutes: int = 10
    post_class_minutes: int = 30
    standby_on_no_class: bool = True


@dataclass
class TeacherConfig:
    teacher_name: str
    courses: list[Course]
    overrides: list[Override]
    window_position: WindowPosition = field(default_factory=WindowPosition)
    settings: Settings = field(default_factory=Settings)
    academic_year: str = ""


def load_teacher_config(path: str | Path) -> TeacherConfig:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    courses = []
    for c in data.get("courses", []):
        if c.get("_out_of_scope"):
            continue
        slots = [Slot(weekday=s["weekday"], period=s["period"]) for s in c.get("slots", [])]
        courses.append(Course(
            id=c["id"],
            name=c["name"],
            course_type=c["course_type"],
            slots=slots,
            course_code=c.get("course_code", ""),
        ))

    overrides = []
    for o in data.get("overrides", []):
        overrides.append(Override(
            type=o["type"],
            course_id=o["course_id"],
            date=o.get("date", ""),
            period=o.get("period"),
            original_date=o.get("original_date", ""),
            original_period=o.get("original_period"),
            new_date=o.get("new_date", ""),
            new_period=o.get("new_period"),
            new_start_time=o.get("new_start_time", ""),
        ))

    wp = data.get("window_position", {})
    settings_data = data.get("settings", {})

    return TeacherConfig(
        teacher_name=data.get("teacher_name", ""),
        academic_year=data.get("academic_year", ""),
        courses=courses,
        overrides=overrides,
        window_position=WindowPosition(x=wp.get("x", 100), y=wp.get("y", 100)),
        settings=Settings(
            pre_class_minutes=settings_data.get("pre_class_minutes", 10),
            post_class_minutes=settings_data.get("post_class_minutes", 30),
            standby_on_no_class=settings_data.get("standby_on_no_class", True),
        ),
    )


def save_teacher_config(config: TeacherConfig, path: str | Path) -> None:
    def _strip_none(d: dict) -> dict:
        return {k: v for k, v in d.items() if v is not None and v != ""}

    data = {
        "teacher_name": config.teacher_name,
        "academic_year": config.academic_year,
        "courses": [
            {
                "id": c.id,
                "name": c.name,
                "course_code": c.course_code,
                "course_type": c.course_type,
                "slots": [{"weekday": s.weekday, "period": s.period} for s in c.slots],
            }
            for c in config.courses
        ],
        "overrides": [
            _strip_none({
                "type": o.type,
                "course_id": o.course_id,
                "date": o.date,
                "period": o.period,
                "original_date": o.original_date,
                "original_period": o.original_period,
                "new_date": o.new_date,
                "new_period": o.new_period,
                "new_start_time": o.new_start_time,
            })
            for o in config.overrides
        ],
        "window_position": {"x": config.window_position.x, "y": config.window_position.y},
        "settings": {
            "pre_class_minutes": config.settings.pre_class_minutes,
            "post_class_minutes": config.settings.post_class_minutes,
            "standby_on_no_class": config.settings.standby_on_no_class,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
