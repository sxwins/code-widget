from __future__ import annotations

from datetime import date

from models.teacher_config import Override
from engine.scheduler import ScheduledClass


def apply_overrides(
    scheduled: list[ScheduledClass],
    overrides: list[Override],
) -> list[ScheduledClass]:
    """
    Apply overrides to scheduled classes and return the updated list.
    After all overrides are applied, session_keys are renumbered by
    actual class order (per course_id + slot_index).
    """
    result = list(scheduled)
    for ov in overrides:
        if ov.type == "skip":
            result = _apply_skip(result, ov)
        elif ov.type == "makeup":
            result = _apply_makeup(result, ov)
        elif ov.type == "reschedule":
            result = _apply_reschedule(result, ov)

    result.sort(key=lambda sc: (sc.date, sc.period))
    return _reassign_session_keys(result)


def _apply_skip(scheduled: list[ScheduledClass], ov: Override) -> list[ScheduledClass]:
    skip_date = date.fromisoformat(ov.date)
    return [
        sc for sc in scheduled
        if not (sc.course_id == ov.course_id and sc.date == skip_date)
    ]


def _apply_makeup(scheduled: list[ScheduledClass], ov: Override) -> list[ScheduledClass]:
    ref = next((sc for sc in scheduled if sc.course_id == ov.course_id), None)
    if ref is None:
        return scheduled
    new_date = date.fromisoformat(ov.date)
    new_sc = ScheduledClass(
        course_id=ref.course_id,
        course_name=ref.course_name,
        date=new_date,
        weekday=new_date.strftime("%A"),
        period=ov.period if ov.period is not None else ref.period,
        session_key="",   # reassigned later
        slot_index=0,
    )
    return scheduled + [new_sc]


def _apply_reschedule(scheduled: list[ScheduledClass], ov: Override) -> list[ScheduledClass]:
    orig_date = date.fromisoformat(ov.original_date)
    result = [
        sc for sc in scheduled
        if not (
            sc.course_id == ov.course_id
            and sc.date == orig_date
            and (ov.original_period is None or sc.period == ov.original_period)
        )
    ]
    ref = next((sc for sc in result if sc.course_id == ov.course_id), None)
    if ref is not None and ov.new_date:
        new_date = date.fromisoformat(ov.new_date)
        if ov.new_start_time:
            new_period = 0
            custom_start = ov.new_start_time
        else:
            new_period = ov.new_period if ov.new_period is not None else ref.period
            custom_start = ""
        new_sc = ScheduledClass(
            course_id=ref.course_id,
            course_name=ref.course_name,
            date=new_date,
            weekday=new_date.strftime("%A"),
            period=new_period,
            session_key="",
            slot_index=0,
            custom_start=custom_start,
        )
        result.append(new_sc)
    return result


def _reassign_session_keys(scheduled: list[ScheduledClass]) -> list[ScheduledClass]:
    """Renumber session_keys "01","02",... per (course_id, slot_index) in date order."""
    groups: dict[tuple[str, int], list[ScheduledClass]] = {}
    for sc in scheduled:
        groups.setdefault((sc.course_id, sc.slot_index), []).append(sc)

    for group in groups.values():
        group.sort(key=lambda s: s.date)
        for i, sc in enumerate(group):
            sc.session_key = f"{i + 1:02d}"

    scheduled.sort(key=lambda sc: (sc.date, sc.period))
    return scheduled
