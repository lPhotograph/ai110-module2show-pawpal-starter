"""Tests for the PawPal+ scheduling logic.

Run from the project root:

    pytest
    pytest --cov

The `sys.path` shim below lets `import pawpal` resolve whether pytest is
launched as `pytest` or `python -m pytest`, without needing a conftest.py.
"""

import sys
from datetime import date, time
from pathlib import Path

# Make the project root importable (this file lives in tests/).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal.pawpal_system import (  # noqa: E402
    Owner,
    Pet,
    Plan,
    Preferences,
    Priority,
    Recurrence,
    Scheduler,
    ScheduledTask,
    Task,
    Timeline,
    TimeWindow,
)

# A fixed reference day. date(2026, 1, 1) is a Thursday (weekday() == 3).
DAY = date(2026, 1, 1)


def make_scheduler(day_start=time(7, 0), day_end=time(21, 0), blocked=None) -> Scheduler:
    """Build a Scheduler with simple day preferences for tests."""
    prefs = Preferences(
        day_start=day_start, day_end=day_end, blocked_windows=blocked or []
    )
    return Scheduler(prefs)


# ---------------------------------------------------------------------------
# TimeWindow
# ---------------------------------------------------------------------------


class TestTimeWindow:
    def test_contains_is_half_open(self):
        w = TimeWindow(time(7, 0), time(9, 0))
        assert w.contains(time(8, 0)) is True
        assert w.contains(time(7, 0)) is True  # start inclusive
        assert w.contains(time(9, 0)) is False  # end exclusive
        assert w.contains(time(6, 59)) is False

    def test_overlaps_but_touching_ends_do_not(self):
        a = TimeWindow(time(7, 0), time(9, 0))
        assert a.overlaps(TimeWindow(time(8, 0), time(10, 0))) is True
        assert a.overlaps(TimeWindow(time(9, 0), time(10, 0))) is False  # touch
        assert a.overlaps(TimeWindow(time(5, 0), time(7, 0))) is False  # touch

    def test_duration_minutes(self):
        assert TimeWindow(time(7, 0), time(7, 30)).duration_minutes() == 30
        assert TimeWindow(time(9, 0), time(12, 0)).duration_minutes() == 180


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------


def test_priority_weight_orders_high_above_low():
    assert Priority.HIGH.weight > Priority.MEDIUM.weight > Priority.LOW.weight


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestTaskDue:
    def test_daily_is_always_due(self):
        assert Task("Walk", 30, recurrence=Recurrence.DAILY).is_due(DAY) is True

    def test_weekly_due_only_on_matching_weekday(self):
        # DAY is a Thursday (weekday 3).
        due = Task("Brush", 15, recurrence=Recurrence.WEEKLY, weekday=3)
        not_due = Task("Brush", 15, recurrence=Recurrence.WEEKLY, weekday=0)
        assert due.is_due(DAY) is True
        assert not_due.is_due(DAY) is False

    def test_once_due_only_on_its_date(self):
        due = Task("Vet", 30, recurrence=Recurrence.ONCE, due_date=DAY)
        not_due = Task("Vet", 30, recurrence=Recurrence.ONCE, due_date=date(2030, 1, 1))
        assert due.is_due(DAY) is True
        assert not_due.is_due(DAY) is False


def test_is_fixed_reflects_fixed_start():
    assert Task("Meds", 10, fixed_start=time(8, 0)).is_fixed() is True
    assert Task("Walk", 30).is_fixed() is False


def test_completion_toggle():
    t = Task("Walk", 30)
    assert t.completed is False
    t.mark_complete()
    assert t.completed is True
    t.reset()
    assert t.completed is False


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------


def test_preferences_is_blocked():
    prefs = Preferences(blocked_windows=[TimeWindow(time(9, 0), time(17, 0))])
    assert prefs.is_blocked(TimeWindow(time(8, 30), time(9, 30))) is True
    assert prefs.is_blocked(TimeWindow(time(7, 0), time(8, 0))) is False


# ---------------------------------------------------------------------------
# Pet + Owner
# ---------------------------------------------------------------------------


def test_add_task_stamps_pet_name():
    pet = Pet("Leo")
    task = pet.add_task(Task("Walk", 30))
    assert task.pet_name == "Leo"
    assert task in pet.tasks


def test_owner_all_tasks_aggregates_across_pets():
    owner = Owner("Jordan")
    leo = owner.add_pet(Pet("Leo"))
    luna = owner.add_pet(Pet("Luna"))
    leo.add_task(Task("Walk", 30))
    luna.add_task(Task("Feed", 10))
    luna.add_task(Task("Play", 20))

    all_tasks = owner.all_tasks()
    assert len(all_tasks) == 3
    assert {t.pet_name for t in all_tasks} == {"Leo", "Luna"}


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


class TestTimeline:
    def test_free_intervals_carve_out_busy(self):
        tl = Timeline(time(7, 0), time(12, 0), busy=[TimeWindow(time(9, 0), time(10, 0))])
        free = tl.free_intervals()
        assert [(w.start, w.end) for w in free] == [
            (time(7, 0), time(9, 0)),
            (time(10, 0), time(12, 0)),
        ]

    def test_find_slot_returns_earliest_fit(self):
        tl = Timeline(time(7, 0), time(12, 0))
        slot = tl.find_slot(30)
        assert (slot.start, slot.end) == (time(7, 0), time(7, 30))

    def test_find_slot_honors_preferred_window(self):
        tl = Timeline(time(7, 0), time(12, 0))
        slot = tl.find_slot(30, preferred=TimeWindow(time(10, 0), time(11, 0)))
        assert slot.start == time(10, 0)

    def test_find_slot_falls_back_when_preferred_full(self):
        # Preferred window is entirely blocked -> fall back to earliest free slot.
        tl = Timeline(
            time(7, 0), time(12, 0), busy=[TimeWindow(time(10, 0), time(11, 0))]
        )
        slot = tl.find_slot(30, preferred=TimeWindow(time(10, 0), time(11, 0)))
        assert slot.start == time(7, 0)

    def test_find_slot_returns_none_when_no_room(self):
        tl = Timeline(time(7, 0), time(8, 0))
        assert tl.find_slot(120) is None

    def test_reserve_prevents_reuse(self):
        tl = Timeline(time(7, 0), time(12, 0))
        first = tl.find_slot(30)
        tl.reserve(first)
        second = tl.find_slot(30)
        assert second.start == time(7, 30)  # moved past the reserved slot


# ---------------------------------------------------------------------------
# Scheduler (the important behaviors)
# ---------------------------------------------------------------------------


class TestScheduler:
    def test_returns_a_plan(self):
        sched = make_scheduler()
        plan = sched.build_plan([Task("Walk", 30)], DAY)
        assert isinstance(plan, Plan)
        assert plan.day == DAY

    def test_fixed_task_placed_at_its_exact_time(self):
        sched = make_scheduler()
        plan = sched.build_plan([Task("Meds", 10, fixed_start=time(8, 0))], DAY)
        assert len(plan.scheduled) == 1
        st = plan.scheduled[0]
        assert (st.start, st.end) == (time(8, 0), time(8, 10))
        assert "fixed" in st.reason.lower()

    def test_higher_priority_scheduled_first(self):
        # Day fits both 30-min tasks exactly (07:00-08:00).
        sched = make_scheduler(day_end=time(8, 0))
        low = Task("Play", 30, priority=Priority.LOW)
        high = Task("Walk", 30, priority=Priority.HIGH)
        plan = sched.build_plan([low, high], DAY)
        assert [st.task.title for st in plan.scheduled] == ["Walk", "Play"]
        assert plan.scheduled[0].start == time(7, 0)

    def test_preferred_window_is_honored(self):
        sched = make_scheduler()
        task = Task("Walk", 30, preferred_window=TimeWindow(time(10, 0), time(12, 0)))
        plan = sched.build_plan([task], DAY)
        st = plan.scheduled[0]
        assert st.start == time(10, 0)  # not 07:00
        assert "preferred" in st.reason.lower()

    def test_task_that_does_not_fit_is_skipped(self):
        sched = make_scheduler(day_end=time(8, 0))  # only 60 minutes available
        plan = sched.build_plan([Task("Grooming", 120)], DAY)
        assert plan.scheduled == []
        assert len(plan.skipped) == 1
        assert plan.skipped[0][0].title == "Grooming"

    def test_completed_task_is_excluded(self):
        sched = make_scheduler()
        done = Task("Walk", 30)
        done.mark_complete()
        plan = sched.build_plan([done], DAY)
        assert plan.scheduled == []
        assert plan.skipped == []  # excluded entirely, not "skipped"

    def test_not_due_task_is_excluded(self):
        sched = make_scheduler()
        task = Task("Vet", 30, recurrence=Recurrence.ONCE, due_date=date(2030, 1, 1))
        plan = sched.build_plan([task], DAY)
        assert plan.scheduled == []
        assert plan.skipped == []

    def test_blocked_window_is_respected(self):
        # Block the first hour; a flexible task should start after it.
        sched = make_scheduler(blocked=[TimeWindow(time(7, 0), time(8, 0))])
        plan = sched.build_plan([Task("Walk", 30)], DAY)
        assert plan.scheduled[0].start == time(8, 0)

    def test_scheduled_tasks_do_not_overlap(self):
        sched = make_scheduler(day_end=time(10, 0))
        tasks = [
            Task("Meds", 10, fixed_start=time(8, 0)),
            Task("Walk", 30, priority=Priority.HIGH),
            Task("Feed", 10, priority=Priority.HIGH),
            Task("Play", 20, priority=Priority.LOW),
        ]
        plan = sched.build_plan(tasks, DAY)
        windows = [TimeWindow(st.start, st.end) for st in plan.scheduled]
        for i, a in enumerate(windows):
            for b in windows[i + 1 :]:
                assert not a.overlaps(b)

    def test_total_minutes_sums_scheduled(self):
        sched = make_scheduler()
        plan = sched.build_plan([Task("Walk", 30), Task("Feed", 10)], DAY)
        assert plan.total_minutes == 40

    def test_summary_mentions_the_day_and_tasks(self):
        sched = make_scheduler()
        plan = sched.build_plan([Task("Walk", 30)], DAY)
        text = plan.summary()
        assert "Daily plan for 2026-01-01" in text
        assert "Walk" in text

    def test_plan_for_owner_pulls_tasks_across_pets(self):
        owner = Owner("Jordan", preferences=Preferences())
        owner.add_pet(Pet("Leo")).add_task(Task("Walk", 30))
        owner.add_pet(Pet("Luna")).add_task(Task("Feed", 10))
        plan = Scheduler(owner.preferences).plan_for_owner(owner, DAY)
        titles = {st.task.title for st in plan.scheduled}
        assert titles == {"Walk", "Feed"}
