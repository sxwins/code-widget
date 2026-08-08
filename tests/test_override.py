"""Tests for engine.override — skip / makeup / reschedule logic."""
from datetime import date
from pathlib import Path

import pytest

from models.school_config import load_school_config
from models.teacher_config import load_teacher_config, Override
from engine.scheduler import resolve_course_schedule
from engine.override import apply_overrides

SCHOOL  = Path(__file__).parent.parent / "config" / "school_config.json"
TEACHER = Path(__file__).parent.parent / "config" / "邵_teacher_config.json"


@pytest.fixture(scope="module")
def school():
    return load_school_config(SCHOOL)


@pytest.fixture(scope="module")
def teacher():
    return load_teacher_config(TEACHER)


@pytest.fixture(scope="module")
def base_scheduled(school, teacher):
    course = next(c for c in teacher.courses if c.id == "EEE1000411")
    return resolve_course_schedule(course, school)


# ---------------------------------------------------------------------------
# Skip
# ---------------------------------------------------------------------------

class TestSkip:
    def test_skip_removes_one_date(self, base_scheduled):
        ov     = Override(type="skip", course_id="EEE1000411", date="2026-04-16")
        result = apply_overrides(base_scheduled, [ov])
        assert len(result) == 13
        assert not any(sc.date == date(2026, 4, 16) for sc in result)

    def test_skip_renumbers_from_01(self, base_scheduled):
        ov     = Override(type="skip", course_id="EEE1000411", date="2026-04-16")
        result = sorted(apply_overrides(base_scheduled, [ov]), key=lambda s: s.date)
        assert result[0].session_key  == "01"
        assert result[-1].session_key == "13"

    def test_skip_wrong_course_no_effect(self, base_scheduled):
        ov     = Override(type="skip", course_id="OTHER", date="2026-04-16")
        result = apply_overrides(base_scheduled, [ov])
        assert len(result) == 14


# ---------------------------------------------------------------------------
# Makeup
# ---------------------------------------------------------------------------

class TestMakeup:
    def test_makeup_adds_date(self, base_scheduled):
        ov     = Override(type="makeup", course_id="EEE1000411", date="2026-08-01", period=1)
        result = apply_overrides(base_scheduled, [ov])
        assert len(result) == 15
        assert any(sc.date == date(2026, 8, 1) for sc in result)

    def test_makeup_session_key_is_last(self, base_scheduled):
        ov     = Override(type="makeup", course_id="EEE1000411", date="2026-08-01", period=1)
        result = sorted(apply_overrides(base_scheduled, [ov]), key=lambda s: s.date)
        assert result[-1].date        == date(2026, 8, 1)
        assert result[-1].session_key == "15"


# ---------------------------------------------------------------------------
# Reschedule
# ---------------------------------------------------------------------------

class TestReschedule:
    def test_reschedule_replaces_date(self, base_scheduled):
        ov = Override(
            type="reschedule",
            course_id="EEE1000411",
            original_date="2026-04-16",
            original_period=1,
            new_date="2026-04-18",
            new_period=2,
        )
        result = apply_overrides(base_scheduled, [ov])
        assert len(result) == 14
        assert not any(sc.date == date(2026, 4, 16) for sc in result)
        assert any(sc.date == date(2026, 4, 18) for sc in result)

    def test_reschedule_new_period(self, base_scheduled):
        ov = Override(
            type="reschedule",
            course_id="EEE1000411",
            original_date="2026-04-16",
            original_period=1,
            new_date="2026-04-18",
            new_period=2,
        )
        result = apply_overrides(base_scheduled, [ov])
        moved = next(sc for sc in result if sc.date == date(2026, 4, 18))
        assert moved.period == 2


# ---------------------------------------------------------------------------
# Q1 multi-slot course (2 slots/week × 7 weeks = 14 sessions)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def q1_scheduled(school, teacher):
    course = next(c for c in teacher.courses if c.id == "RD010001E3")
    return resolve_course_schedule(course, school)


class TestQ1MultiSlot:
    def test_q1_keys_sequential_01_to_14(self, q1_scheduled):
        result = sorted(apply_overrides(list(q1_scheduled), []), key=lambda s: (s.date, s.period))
        assert [s.session_key for s in result] == [f"{n:02d}" for n in range(1, 15)]

    def test_q1_week1_slot0_is_01_slot1_is_02(self, q1_scheduled):
        result = sorted(apply_overrides(list(q1_scheduled), []), key=lambda s: (s.date, s.period))
        assert result[0].session_key == "01"   # 2026-04-15 Wed period=2
        assert result[1].session_key == "02"   # 2026-04-17 Fri period=3

    def test_q1_skip_renumbers_to_13(self, q1_scheduled):
        ov = Override(type="skip", course_id="RD010001E3", date="2026-04-15")
        result = sorted(apply_overrides(list(q1_scheduled), [ov]), key=lambda s: (s.date, s.period))
        assert len(result) == 13
        assert [s.session_key for s in result] == [f"{n:02d}" for n in range(1, 14)]


# ---------------------------------------------------------------------------
# TD-04 — malformed date strings must not crash; bad records are silently skipped
# ---------------------------------------------------------------------------

class TestMalformedDates:
    def test_skip_bad_date_no_crash(self, base_scheduled):
        ov = Override(type="skip", course_id="EEE1000411", date="2026/04/16")
        result = apply_overrides(list(base_scheduled), [ov])
        assert len(result) == 14  # unchanged

    def test_makeup_bad_date_no_crash(self, base_scheduled):
        ov = Override(type="makeup", course_id="EEE1000411", date="invalid")
        result = apply_overrides(list(base_scheduled), [ov])
        assert len(result) == 14  # unchanged

    def test_reschedule_bad_original_date_no_crash(self, base_scheduled):
        ov = Override(
            type="reschedule", course_id="EEE1000411",
            original_date="2026/04/16", new_date="2026-04-18", new_period=2,
        )
        result = apply_overrides(list(base_scheduled), [ov])
        assert len(result) == 14  # unchanged — original not removed, replacement not added

    def test_reschedule_bad_new_date_removes_original_only(self, base_scheduled):
        ov = Override(
            type="reschedule", course_id="EEE1000411",
            original_date="2026-04-16", original_period=1,
            new_date="2026/04/18", new_period=2,
        )
        result = apply_overrides(list(base_scheduled), [ov])
        assert len(result) == 13  # original removed, replacement skipped
        assert not any(sc.date == date(2026, 4, 16) for sc in result)
