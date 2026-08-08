"""Tests for engine.scheduler — date resolution and display window logic."""
from datetime import date, datetime
from pathlib import Path

import pytest

from models.school_config import load_school_config
from models.teacher_config import load_teacher_config, Settings
from engine.scheduler import resolve_course_schedule, compute_window, get_active_class

SCHOOL  = Path(__file__).parent.parent / "config" / "school_config.json"
TEACHER = Path(__file__).parent.parent / "config" / "邵_teacher_config.json"


@pytest.fixture(scope="module")
def school():
    return load_school_config(SCHOOL)


@pytest.fixture(scope="module")
def teacher():
    return load_teacher_config(TEACHER)


# ---------------------------------------------------------------------------
# Session count
# ---------------------------------------------------------------------------

class TestSessionCount:
    def test_spring_course_14_sessions(self, school, teacher):
        # 初年次セミナーA: spring, Thu-1 → 14 dates
        course = next(c for c in teacher.courses if c.id == "EEE1000411")
        assert len(resolve_course_schedule(course, school)) == 14

    def test_autumn_course_14_sessions(self, school, teacher):
        # データ分析入門: autumn, Mon-3 → 14 dates
        course = next(c for c in teacher.courses if c.id == "RD01000503")
        assert len(resolve_course_schedule(course, school)) == 14

    def test_q1_course_14_occasions(self, school, teacher):
        # 情報リテラシーA: Q1, Wed-2 + Fri-3 → 7 sessions × 2 slots = 14
        course = next(c for c in teacher.courses if c.id == "RD010001E3")
        assert len(resolve_course_schedule(course, school)) == 14

    def test_q1_session_keys_sequential(self, school, teacher):
        # Session keys for Q1 must be 01..14 (not 01..07 duplicated per slot)
        course = next(c for c in teacher.courses if c.id == "RD010001E3")
        scheduled = sorted(resolve_course_schedule(course, school), key=lambda s: (s.date, s.period))
        keys = [s.session_key for s in scheduled]
        assert keys == [f"{n:02d}" for n in range(1, 15)]

    def test_q1_week1_slot0_session01_slot1_session02(self, school, teacher):
        # In week 1: Wednesday (slot 0) → 01, Friday (slot 1) → 02
        course = next(c for c in teacher.courses if c.id == "RD010001E3")
        scheduled = sorted(resolve_course_schedule(course, school), key=lambda s: (s.date, s.period))
        assert scheduled[0].session_key == "01" and scheduled[0].slot_index == 0
        assert scheduled[1].session_key == "02" and scheduled[1].slot_index == 1

    def test_intensive_returns_empty(self, school):
        from models.teacher_config import Course, Slot
        intensive = Course(id="x", name="x", course_type="intensive", slots=[])
        assert resolve_course_schedule(intensive, school) == []


# ---------------------------------------------------------------------------
# Correct dates
# ---------------------------------------------------------------------------

class TestCourseDates:
    def test_spring_thu1_first_date(self, school, teacher):
        # 初年次セミナーA spring Thu-1: first session = 2026-04-16
        course = next(c for c in teacher.courses if c.id == "EEE1000411")
        scheduled = sorted(resolve_course_schedule(course, school), key=lambda s: s.date)
        assert scheduled[0].date  == date(2026, 4, 16)
        assert scheduled[0].session_key == "01"
        assert scheduled[0].period == 1

    def test_spring_thu1_last_date(self, school, teacher):
        # Last session = 2026-07-23
        course = next(c for c in teacher.courses if c.id == "EEE1000411")
        scheduled = sorted(resolve_course_schedule(course, school), key=lambda s: s.date)
        assert scheduled[-1].date == date(2026, 7, 23)
        assert scheduled[-1].session_key == "14"

    def test_q1_slot0_is_wednesday_period2(self, school, teacher):
        course = next(c for c in teacher.courses if c.id == "RD010001E3")
        slot0 = [s for s in resolve_course_schedule(course, school) if s.slot_index == 0]
        assert len(slot0) == 7
        assert all(s.weekday == "Wednesday" and s.period == 2 for s in slot0)

    def test_q1_slot1_is_friday_period3(self, school, teacher):
        course = next(c for c in teacher.courses if c.id == "RD010001E3")
        slot1 = [s for s in resolve_course_schedule(course, school) if s.slot_index == 1]
        assert len(slot1) == 7
        assert all(s.weekday == "Friday" and s.period == 3 for s in slot1)

    def test_q1_first_wednesday(self, school, teacher):
        # Q1 Wed-2 first session = 2026-04-15
        course = next(c for c in teacher.courses if c.id == "RD010001E3")
        slot0 = sorted(
            [s for s in resolve_course_schedule(course, school) if s.slot_index == 0],
            key=lambda s: s.date,
        )
        assert slot0[0].date == date(2026, 4, 15)

    def test_autumn_mon3_first_date(self, school, teacher):
        # データ分析入門 autumn Mon-3: first session = 2026-09-28
        course = next(c for c in teacher.courses if c.id == "RD01000503")
        scheduled = sorted(resolve_course_schedule(course, school), key=lambda s: s.date)
        assert scheduled[0].date == date(2026, 9, 28)


# ---------------------------------------------------------------------------
# Display window
# ---------------------------------------------------------------------------

class TestDisplayWindow:
    def test_period1_window(self, school, teacher):
        # 初年次セミナーA, 2026-04-16, period 1 (start 08:50)
        # window: 08:40 ~ 09:20
        course   = next(c for c in teacher.courses if c.id == "EEE1000411")
        sc       = sorted(resolve_course_schedule(course, school), key=lambda s: s.date)[0]
        settings = Settings(pre_class_minutes=10, post_class_minutes=30)
        ws, we   = compute_window(sc, school, settings)
        assert ws == datetime(2026, 4, 16, 8, 40)
        assert we == datetime(2026, 4, 16, 9, 20)

    def test_active_inside_window(self, school, teacher):
        course    = next(c for c in teacher.courses if c.id == "EEE1000411")
        scheduled = resolve_course_schedule(course, school)
        settings  = Settings()
        active = get_active_class(datetime(2026, 4, 16, 8, 45), scheduled, school, settings)
        assert active is not None
        assert active.course_id == "EEE1000411"

    def test_active_at_window_boundary_start(self, school, teacher):
        course    = next(c for c in teacher.courses if c.id == "EEE1000411")
        scheduled = resolve_course_schedule(course, school)
        settings  = Settings()
        active = get_active_class(datetime(2026, 4, 16, 8, 40), scheduled, school, settings)
        assert active is not None

    def test_no_active_before_window(self, school, teacher):
        course    = next(c for c in teacher.courses if c.id == "EEE1000411")
        scheduled = resolve_course_schedule(course, school)
        settings  = Settings()
        active = get_active_class(datetime(2026, 4, 16, 8, 39), scheduled, school, settings)
        assert active is None

    def test_no_active_on_non_class_day(self, school, teacher):
        course    = next(c for c in teacher.courses if c.id == "EEE1000411")
        scheduled = resolve_course_schedule(course, school)
        settings  = Settings()
        # 2026-04-20 (Monday) has no Thursday class
        active = get_active_class(datetime(2026, 4, 20, 8, 50), scheduled, school, settings)
        assert active is None


# ---------------------------------------------------------------------------
# TD-04 — malformed custom_start raises descriptive ValueError
# ---------------------------------------------------------------------------

class TestCustomStartParsing:
    def _make_sc_custom(self, custom_start: str):
        from engine.scheduler import ScheduledClass
        return ScheduledClass(
            course_id="X", course_name="X",
            date=date(2026, 4, 16), weekday="Thursday",
            period=0, session_key="01", slot_index=0,
            custom_start=custom_start,
        )

    def test_valid_custom_start(self, school):
        sc = self._make_sc_custom("09:30")
        ws, we = compute_window(sc, school, Settings())
        assert ws.hour == 9 and ws.minute == 20  # 09:30 − 10 min pre

    def test_malformed_custom_start_raises_valueerror(self, school):
        sc = self._make_sc_custom("abc")
        with pytest.raises(ValueError, match="custom_start"):
            compute_window(sc, school, Settings())

    def test_no_colon_custom_start_raises_valueerror(self, school):
        sc = self._make_sc_custom("0930")
        with pytest.raises(ValueError, match="custom_start"):
            compute_window(sc, school, Settings())
