# テスト実行ログ

**日付**：2026-08-08  
**環境**：Ubuntu 24.04 (Docker) / Python 3.12.3 / pytest 9.0.2 / PySide6 6.10.2  
**実行コマンド**：
```bash
uv run pytest tests/test_override.py tests/test_scheduler.py -v --tb=short
QT_QPA_PLATFORM=offscreen uv run pytest tests/test_attendance_window.py tests/test_tray.py tests/test_config_dialog.py -v --tb=short
```

---

## 結果サマリー

| カテゴリ | テスト数 | 結果 |
|---------|---------|------|
| エンジン（override / scheduler） | 34 | ✅ 全通過 |
| GUI（attendance_window / tray / config_dialog） | 13 | ✅ 全通過 |
| **合計** | **47** | **✅ 47 passed, 0 failed** |

---

## エンジンテスト詳細（34件）

```
tests/test_override.py::TestSkip::test_skip_removes_one_date              PASSED
tests/test_override.py::TestSkip::test_skip_renumbers_from_01             PASSED
tests/test_override.py::TestSkip::test_skip_wrong_course_no_effect        PASSED
tests/test_override.py::TestMakeup::test_makeup_adds_date                 PASSED
tests/test_override.py::TestMakeup::test_makeup_session_key_is_last       PASSED
tests/test_override.py::TestReschedule::test_reschedule_replaces_date     PASSED
tests/test_override.py::TestReschedule::test_reschedule_new_period        PASSED
tests/test_override.py::TestQ1MultiSlot::test_q1_keys_sequential_01_to_14 PASSED
tests/test_override.py::TestQ1MultiSlot::test_q1_week1_slot0_is_01_slot1_is_02 PASSED
tests/test_override.py::TestQ1MultiSlot::test_q1_skip_renumbers_to_13    PASSED
tests/test_override.py::TestMalformedDates::test_skip_bad_date_no_crash   PASSED
tests/test_override.py::TestMalformedDates::test_makeup_bad_date_no_crash PASSED
tests/test_override.py::TestMalformedDates::test_reschedule_bad_original_date_no_crash PASSED
tests/test_override.py::TestMalformedDates::test_reschedule_bad_new_date_removes_original_only PASSED
tests/test_scheduler.py::TestSessionCount::test_spring_course_14_sessions PASSED
tests/test_scheduler.py::TestSessionCount::test_autumn_course_14_sessions PASSED
tests/test_scheduler.py::TestSessionCount::test_q1_course_14_occasions    PASSED
tests/test_scheduler.py::TestSessionCount::test_q1_session_keys_sequential PASSED
tests/test_scheduler.py::TestSessionCount::test_q1_week1_slot0_session01_slot1_session02 PASSED
tests/test_scheduler.py::TestSessionCount::test_intensive_returns_empty   PASSED
tests/test_scheduler.py::TestCourseDates::test_spring_thu1_first_date     PASSED
tests/test_scheduler.py::TestCourseDates::test_spring_thu1_last_date      PASSED
tests/test_scheduler.py::TestCourseDates::test_q1_slot0_is_wednesday_period2 PASSED
tests/test_scheduler.py::TestCourseDates::test_q1_slot1_is_friday_period3 PASSED
tests/test_scheduler.py::TestCourseDates::test_q1_first_wednesday         PASSED
tests/test_scheduler.py::TestCourseDates::test_autumn_mon3_first_date     PASSED
tests/test_scheduler.py::TestDisplayWindow::test_period1_window           PASSED
tests/test_scheduler.py::TestDisplayWindow::test_active_inside_window     PASSED
tests/test_scheduler.py::TestDisplayWindow::test_active_at_window_boundary_start PASSED
tests/test_scheduler.py::TestDisplayWindow::test_no_active_before_window  PASSED
tests/test_scheduler.py::TestDisplayWindow::test_no_active_on_non_class_day PASSED
tests/test_scheduler.py::TestCustomStartParsing::test_valid_custom_start  PASSED
tests/test_scheduler.py::TestCustomStartParsing::test_malformed_custom_start_raises_valueerror PASSED
tests/test_scheduler.py::TestCustomStartParsing::test_no_colon_custom_start_raises_valueerror PASSED
```

## GUIテスト詳細（13件）

```
tests/test_attendance_window.py::test_update_class_sets_labels            PASSED
tests/test_attendance_window.py::test_update_class_sets_code              PASSED
tests/test_attendance_window.py::test_initial_state_hidden                PASSED
tests/test_tray.py::test_tray_creates_without_error                       PASSED
tests/test_tray.py::test_tray_tooltip_no_class                            PASSED
tests/test_tray.py::test_tray_tooltip_active_class                        PASSED
tests/test_tray.py::test_toggle_label_shows_hide_when_window_visible      PASSED
tests/test_tray.py::test_toggle_label_shows_display_when_window_hidden    PASSED
tests/test_config_dialog.py::test_dialog_opens                            PASSED
tests/test_config_dialog.py::test_courses_tab_row_count                   PASSED
tests/test_config_dialog.py::test_year_column                             PASSED
tests/test_config_dialog.py::test_tab_count                               PASSED
tests/test_config_dialog.py::test_adj_tab_buttons                         PASSED
```

---

## 今回追加したテスト（本セッション）

| テスト | 対応修正 |
|--------|---------|
| `TestMalformedDates` (4件) | TD-04：日付解析容错 |
| `TestCustomStartParsing` (3件) | TD-04：custom_start 解析容错 |
| `test_toggle_label_shows_hide_when_window_visible` | tray メニューラベル修正 |
| `test_toggle_label_shows_display_when_window_hidden` | tray メニューラベル修正 |
