"""scheduler.py — resolve course schedules from school config and compute display windows.

Key concepts:
  - ScheduledClass: one concrete class occurrence (date + period + session number)
  - resolve_course_schedule: expands a Course into all its ScheduledClass entries for the semester
  - compute_window: returns the [window_start, window_end] datetime range for showing the overlay
  - get_active_class: given the current time, returns whichever class is in its display window
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from models.school_config import SchoolConfig
from models.teacher_config import Course, Settings


@dataclass
class ScheduledClass:
    course_id: str
    course_name: str
    date: date
    weekday: str      # "Monday" / ...
    period: int       # 1~6
    session_key: str  # "01"~"14"
    slot_index: int   # 0 or 1 (Q courses have 2 slots)
    custom_start: str = ""  # HH:MM, overrides period start if set


def resolve_course_schedule(
    course: Course,
    school_config: SchoolConfig,
) -> list[ScheduledClass]:
    """Return all ScheduledClass entries for a course (before overrides)."""
    if course.course_type == "intensive":
        return []

    ct = school_config.course_types.get(course.course_type)
    if ct is None:
        return []

    semester = school_config.get_semester(ct.semester_id)
    if semester is None:
        return []

    result: list[ScheduledClass] = []
    if ct.slots_per_week > 1:
        # Multi-slot weeks (Q courses): iterate weeks × slots so session numbers
        # are sequential across both slots.  Week 1 → sessions 01,02;
        # week 2 → sessions 03,04; …; week 7 → sessions 13,14.
        for week_idx, week_key in enumerate(ct.session_keys):
            for slot_idx, slot in enumerate(course.slots):
                wd_dates = semester.weekday_dates.get(slot.weekday, {})
                date_str = wd_dates.get(week_key)
                if date_str is None:
                    continue
                actual_num = week_idx * ct.slots_per_week + slot_idx + 1
                result.append(ScheduledClass(
                    course_id=course.id,
                    course_name=course.name,
                    date=date.fromisoformat(date_str),
                    weekday=slot.weekday,
                    period=slot.period,
                    session_key=f"{actual_num:02d}",
                    slot_index=slot_idx,
                ))
    else:
        for slot_idx, slot in enumerate(course.slots):
            wd_dates = semester.weekday_dates.get(slot.weekday, {})
            for session_key in ct.session_keys:
                date_str = wd_dates.get(session_key)
                if date_str is None:
                    continue
                result.append(ScheduledClass(
                    course_id=course.id,
                    course_name=course.name,
                    date=date.fromisoformat(date_str),
                    weekday=slot.weekday,
                    period=slot.period,
                    session_key=session_key,
                    slot_index=slot_idx,
                ))

    return result


def compute_window(
    sc: ScheduledClass,
    school_config: SchoolConfig,
    settings: Settings,
) -> tuple[datetime, datetime]:
    """Return (window_start, window_end) for a ScheduledClass."""
    if sc.custom_start:
        try:
            h, m = map(int, sc.custom_start.split(":"))
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid custom_start format {sc.custom_start!r} for course {sc.course_id!r}. "
                "Expected HH:MM (e.g. \"09:00\")."
            )
    else:
        period_info = school_config.periods[str(sc.period)]
        h, m = map(int, period_info.start.split(":"))
    class_start = datetime.combine(sc.date, time(h, m))
    window_start = class_start - timedelta(minutes=settings.pre_class_minutes)
    window_end   = class_start + timedelta(minutes=settings.post_class_minutes)
    return window_start, window_end


def get_active_class(
    now: datetime,
    scheduled_classes: list[ScheduledClass],
    school_config: SchoolConfig,
    settings: Settings,
) -> ScheduledClass | None:
    """
    Return the ScheduledClass whose window covers `now`.
    If multiple match: prefer closest window_start to now, then lower period.
    Returns None if nothing is active.
    """
    candidates: list[tuple[ScheduledClass, datetime]] = []
    for sc in scheduled_classes:
        ws, we = compute_window(sc, school_config, settings)
        if ws <= now <= we:
            candidates.append((sc, ws))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (abs((now - x[1]).total_seconds()), x[0].period))
    return candidates[0][0]
