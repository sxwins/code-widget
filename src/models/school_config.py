from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Period:
    start: str  # "HH:MM"
    end: str    # "HH:MM"


@dataclass
class CourseType:
    name: str
    semester_id: str
    session_keys: list[str]   # e.g. ["01".."14"] or ["01".."07"]
    slots_per_week: int


@dataclass
class SemesterDates:
    semester_id: str
    semester_name: str
    semester_start: str  # "YYYY-MM-DD"
    semester_end: str    # "YYYY-MM-DD"
    # weekday_dates[weekday]["01".."14"] = "YYYY-MM-DD"
    weekday_dates: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class SchoolConfig:
    periods: dict[str, Period]           # key: "1"~"6"
    course_types: dict[str, CourseType]  # key: "spring","autumn","Q1"~"Q4"
    semesters: list[SemesterDates]

    def get_semester(self, semester_id: str) -> SemesterDates | None:
        for s in self.semesters:
            if s.semester_id == semester_id:
                return s
        return None


def load_school_config(path: str | Path) -> SchoolConfig:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    periods = {k: Period(**v) for k, v in data["periods"].items()}

    course_types = {
        k: CourseType(
            name=v["name"],
            semester_id=v["semester_id"],
            session_keys=v["session_keys"],
            slots_per_week=v["slots_per_week"],
        )
        for k, v in data["course_types"].items()
    }

    semesters = [
        SemesterDates(
            semester_id=s["semester_id"],
            semester_name=s["semester_name"],
            semester_start=s["semester_start"],
            semester_end=s["semester_end"],
            weekday_dates=s["weekday_dates"],
        )
        for s in data["semesters"]
    ]

    return SchoolConfig(periods=periods, course_types=course_types, semesters=semesters)
