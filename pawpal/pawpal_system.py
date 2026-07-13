"""PawPal+ logic layer.

All backend classes live here, kept separate from the Streamlit UI (`app.py`)
so the scheduling logic stays a pure, testable transformation.

The four main classes (per the project spec):
  * Task      - a single care activity (what, how long, how often, done or not).
  * Pet       - pet details plus the list of tasks that belong to it.
  * Owner     - manages multiple pets and exposes all their tasks together.
  * Scheduler - the "brain": retrieves due tasks across pets, organizes them by
                priority/time, and builds an explainable daily Plan.

Supporting types: the Priority / TaskType / Recurrence enums, TimeWindow,
Preferences, ScheduledTask, Plan, and Timeline (the free/busy day model the
Scheduler places tasks onto).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from enum import Enum


# ---------------------------------------------------------------------------
# Small time helpers (work in minutes-since-midnight; `time` is awkward to add)
# ---------------------------------------------------------------------------


def _to_minutes(t: time) -> int:
    """Convert a `time` to minutes since midnight."""
    return t.hour * 60 + t.minute


def _to_time(minutes: int) -> time:
    """Convert minutes since midnight back to a `time` (clamped to a valid day)."""
    minutes = max(0, min(23 * 60 + 59, minutes))
    return time(minutes // 60, minutes % 60)


# ---------------------------------------------------------------------------
# Enums (replace magic strings)
# ---------------------------------------------------------------------------


class Priority(Enum):
    """Task priority. `weight` is used by the scheduler to sort tasks."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @property
    def weight(self) -> int:
        """Numeric weight for sorting (higher = more important)."""
        return self.value


class TaskType(Enum):
    """Category of care task. Useful for grouping and default durations."""

    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    GROOMING = "grooming"
    ENRICHMENT = "enrichment"
    OTHER = "other"


class Recurrence(Enum):
    """How often a task repeats."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


# ---------------------------------------------------------------------------
# TimeWindow + Preferences
# ---------------------------------------------------------------------------


@dataclass
class TimeWindow:
    """A span of time within a day, e.g. a preferred slot or a blocked period."""

    start: time
    end: time

    def contains(self, t: time) -> bool:
        """Return True if `t` falls within [start, end)."""
        return _to_minutes(self.start) <= _to_minutes(t) < _to_minutes(self.end)

    def overlaps(self, other: "TimeWindow") -> bool:
        """Return True if this window overlaps `other` (touching ends do not)."""
        return _to_minutes(self.start) < _to_minutes(other.end) and _to_minutes(
            other.start
        ) < _to_minutes(self.end)

    def duration_minutes(self) -> int:
        """Length of the window in minutes."""
        return _to_minutes(self.end) - _to_minutes(self.start)


@dataclass
class Preferences:
    """Owner-level scheduling constraints for a day.

    The day's available time is modeled as a real timeline: the span
    [day_start, day_end) minus any `blocked_windows`. There is deliberately no
    separate `available_minutes` budget -- the clock and blocked windows are the
    single source of truth for "time available" (see Timeline).
    """

    day_start: time = time(7, 0)
    day_end: time = time(22, 0)
    blocked_windows: list[TimeWindow] = field(default_factory=list)

    def is_blocked(self, window: TimeWindow) -> bool:
        """Return True if `window` overlaps any blocked window."""
        return any(window.overlaps(b) for b in self.blocked_windows)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


@dataclass
class Task:
    """A single care activity.

    A Task describes *what needs to happen* (and how often / whether it's done);
    it does not know *when* it will run today -- placement is decided by the
    Scheduler, which produces a ScheduledTask.

    `pet_name` is a label linking the task back to its pet; it is set
    automatically by `Pet.add_task`, so a flat list of tasks is still
    self-describing when the Scheduler flattens tasks across pets.

    Recurrence anchors:
      * DAILY  -> due every day.
      * WEEKLY -> due when `day.weekday() == weekday` (0=Mon .. 6=Sun).
      * ONCE   -> due only on `due_date`.

    `not_before` suppresses a task until a given date. It is set on the *next*
    occurrence spawned when a recurring task is completed, so completing today's
    walk does not make it due again today (see `next_occurrence`).
    """

    title: str
    duration_minutes: int
    pet_name: str = ""
    priority: Priority = Priority.MEDIUM
    task_type: TaskType = TaskType.OTHER
    preferred_window: TimeWindow | None = None
    fixed_start: time | None = None
    recurrence: Recurrence = Recurrence.DAILY
    due_date: date | None = None  # anchor for ONCE
    weekday: int | None = None  # anchor for WEEKLY (0=Mon .. 6=Sun)
    completed: bool = False
    not_before: date | None = None  # earliest day this occurrence may be scheduled

    def is_due(self, day: date) -> bool:
        """Return True if this task should be scheduled on `day`."""
        if self.not_before is not None and day < self.not_before:
            return False
        if self.recurrence is Recurrence.DAILY:
            return True
        if self.recurrence is Recurrence.WEEKLY:
            return self.weekday is not None and day.weekday() == self.weekday
        if self.recurrence is Recurrence.ONCE:
            return self.due_date is not None and day == self.due_date
        return False

    def is_fixed(self) -> bool:
        """Return True if the task must start at a specific time."""
        return self.fixed_start is not None

    def mark_complete(self) -> None:
        """Mark this task done (the scheduler will not place completed tasks)."""
        self.completed = True

    def reset(self) -> None:
        """Mark this task not-done again (e.g. at the start of a new day)."""
        self.completed = False

    def next_occurrence(self, completed_on: date) -> "Task | None":
        """Build the next occurrence after completing this task on `completed_on`.

        Returns a fresh, not-completed copy for DAILY (next day) and WEEKLY
        (next week) tasks; returns None for ONCE tasks (they do not repeat).
        """
        if self.recurrence is Recurrence.DAILY:
            gap = timedelta(days=1)
        elif self.recurrence is Recurrence.WEEKLY:
            gap = timedelta(days=7)
        else:  # ONCE
            return None
        return replace(self, completed=False, not_before=completed_on + gap)


# ---------------------------------------------------------------------------
# Pet + Owner
# ---------------------------------------------------------------------------


@dataclass
class Pet:
    """Stores pet details and the list of tasks that belong to this pet."""

    name: str
    species: str = "dog"
    breed: str = ""
    age: int | None = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> Task:
        """Attach `task` to this pet (stamping its `pet_name`) and return it."""
        task.pet_name = self.name
        self.tasks.append(task)
        return task

    def remove_task(self, task: Task) -> None:
        """Detach `task` from this pet if present."""
        if task in self.tasks:
            self.tasks.remove(task)

    def complete_task(self, task: Task, on: date) -> Task | None:
        """Mark `task` done and, if it recurs, append its next occurrence.

        Returns the newly created next-occurrence task (added to this pet), or
        None if the task does not repeat.
        """
        task.mark_complete()
        nxt = task.next_occurrence(on)
        if nxt is not None:
            self.tasks.append(nxt)
        return nxt


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    name: str
    preferences: Preferences = field(default_factory=Preferences)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet with this owner and return it."""
        self.pets.append(pet)
        return pet

    def all_tasks(self) -> list[Task]:
        """Return every task across all pets as one flat list."""
        return [task for pet in self.pets for task in pet.tasks]

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[Task]:
        """Return tasks across all pets, optionally filtered.

        Pass `pet_name` to keep only one pet's tasks, and/or `completed` to keep
        only done (`True`) or pending (`False`) tasks. `None` means "don't filter
        on that field".
        """
        tasks = self.all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks


# ---------------------------------------------------------------------------
# Scheduler outputs
# ---------------------------------------------------------------------------


@dataclass
class ScheduledTask:
    """A Task placed on the timeline at a concrete start/end time."""

    task: Task
    start: time
    end: time
    reason: str = ""  # why the scheduler placed it here - powers the explanation


@dataclass
class Plan:
    """The output of the scheduler for a single day."""

    day: date
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[Task, str]] = field(default_factory=list)  # (task, why skipped)
    warnings: list[str] = field(default_factory=list)  # e.g. fixed-time clashes

    @property
    def total_minutes(self) -> int:
        """Total minutes of scheduled tasks."""
        return sum(st.task.duration_minutes for st in self.scheduled)

    def summary(self) -> str:
        """Human-readable summary of the plan (for CLI/Streamlit display)."""
        lines = [f"Daily plan for {self.day.isoformat()}:"]
        if self.scheduled:
            for st in self.scheduled:
                t = st.task
                who = f"{t.pet_name}'s " if t.pet_name else ""
                lines.append(
                    f"  {st.start:%H:%M}-{st.end:%H:%M}  {who}{t.title} "
                    f"({t.duration_minutes} min) [{t.priority.name.lower()}]"
                    f" - {st.reason}"
                )
        else:
            lines.append("  (nothing scheduled)")
        if self.skipped:
            lines.append("Skipped:")
            for task, why in self.skipped:
                who = f"{task.pet_name}'s " if task.pet_name else ""
                lines.append(
                    f"  {who}{task.title} ({task.duration_minutes} min) - {why}"
                )
        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  ! {warning}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Timeline (free/busy day model) + Scheduler
# ---------------------------------------------------------------------------


@dataclass
class Timeline:
    """Free/busy model of a single day, used to place tasks without overlaps.

    Built from the owner's day bounds with blocked windows pre-marked as busy.
    The scheduler reserves a slot every time it places a task, so overlaps,
    fixed times, blocked windows, and preferred windows are all handled by this
    one structure.
    """

    day_start: time
    day_end: time
    busy: list[TimeWindow] = field(default_factory=list)  # occupied + blocked slots

    def free_intervals(self) -> list[TimeWindow]:
        """Return the gaps between busy windows within [day_start, day_end)."""
        lo, hi = _to_minutes(self.day_start), _to_minutes(self.day_end)
        # Clip busy windows to the day and drop anything empty/out of range.
        spans = sorted(
            (max(lo, _to_minutes(b.start)), min(hi, _to_minutes(b.end)))
            for b in self.busy
        )
        spans = [(s, e) for s, e in spans if s < e]

        free: list[TimeWindow] = []
        cursor = lo
        for s, e in spans:
            if s > cursor:
                free.append(TimeWindow(_to_time(cursor), _to_time(s)))
            cursor = max(cursor, e)
        if cursor < hi:
            free.append(TimeWindow(_to_time(cursor), _to_time(hi)))
        return free

    def find_slot(
        self, duration_minutes: int, preferred: TimeWindow | None = None
    ) -> TimeWindow | None:
        """Find the earliest free slot that fits `duration_minutes`.

        Honors `preferred` as a *soft* preference: try to land inside it first,
        then fall back to the earliest free slot anywhere. Returns None if
        nothing fits.
        """
        free = self.free_intervals()

        if preferred is not None:
            p_lo, p_hi = _to_minutes(preferred.start), _to_minutes(preferred.end)
            for iv in free:  # already earliest-first
                s = max(_to_minutes(iv.start), p_lo)
                e = min(_to_minutes(iv.end), p_hi)
                if e - s >= duration_minutes:
                    return TimeWindow(_to_time(s), _to_time(s + duration_minutes))

        for iv in free:
            if iv.duration_minutes() >= duration_minutes:
                start = _to_minutes(iv.start)
                return TimeWindow(_to_time(start), _to_time(start + duration_minutes))
        return None

    def reserve(self, window: TimeWindow) -> None:
        """Mark `window` busy so later placements do not overlap it."""
        self.busy.append(window)


class Scheduler:
    """Builds a daily Plan from tasks and owner preferences.

    v1 algorithm (greedy, explainable):
      1. Filter to tasks that are due on `day` and not already completed.
      2. Build a Timeline for the day and mark blocked windows busy.
      3. Place all fixed-start tasks first, reserving their exact slots
         (hard constraint); skip any that fall out of bounds or collide.
      4. Sort the remaining tasks by (priority desc, duration asc).
      5. For each, ask the Timeline for a slot -- honoring the preferred window
         as a *soft* preference. Reserve it and record a `reason`.
      6. Anything with no available slot -> Plan.skipped with a reason.
    """

    def __init__(self, preferences: Preferences) -> None:
        """Create a scheduler bound to the owner's day `preferences`."""
        self.preferences = preferences

    def plan_for_owner(self, owner: Owner, day: date) -> Plan:
        """Convenience: schedule every task across all of `owner`'s pets."""
        return self.build_plan(owner.all_tasks(), day)

    def build_plan(self, tasks: list[Task], day: date) -> Plan:
        """Produce a Plan for `day` from `tasks`. Main entry point."""
        plan = Plan(day=day)
        timeline = self._build_timeline(day)

        due = self._due_tasks(tasks, day)
        plan.warnings = self.detect_conflicts(due, day)

        fixed = sorted(
            (t for t in due if t.is_fixed()), key=lambda t: _to_minutes(t.fixed_start)
        )
        flexible = self.sort_tasks([t for t in due if not t.is_fixed()])

        # 3. Fixed-time tasks claim their exact slots first.
        for task in fixed:
            scheduled = self._place_fixed(task, timeline)
            if scheduled is None:
                plan.skipped.append(
                    (task, f"Fixed time {task.fixed_start:%H:%M} does not fit "
                     "(outside the day or conflicts with another commitment).")
                )
            else:
                plan.scheduled.append(scheduled)

        # 5. Flexible tasks fill the remaining gaps, highest priority first.
        for task in flexible:
            scheduled = self._place(task, timeline)
            if scheduled is None:
                plan.skipped.append(
                    (task, f"No open {task.duration_minutes}-min slot remained today.")
                )
            else:
                plan.scheduled.append(scheduled)

        plan.scheduled.sort(key=lambda st: _to_minutes(st.start))
        return plan

    # -- helpers ------------------------------------------------------------

    def _due_tasks(self, tasks: list[Task], day: date) -> list[Task]:
        """Filter to tasks that recur on `day` and are not already done."""
        return [t for t in tasks if t.is_due(day) and not t.completed]

    def _build_timeline(self, day: date) -> Timeline:
        """Create a Timeline for `day` from preferences (bounds - blocked)."""
        return Timeline(
            day_start=self.preferences.day_start,
            day_end=self.preferences.day_end,
            busy=list(self.preferences.blocked_windows),
        )

    @staticmethod
    def sort_tasks(tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (highest first), then shorter duration first."""
        return sorted(tasks, key=lambda t: (-t.priority.weight, t.duration_minutes))

    def detect_conflicts(self, tasks: list[Task], day: date) -> list[str]:
        """Return warning messages for fixed-time tasks that clash on `day`.

        Lightweight, pairwise check: only fixed-start tasks assert a specific
        time (flexible tasks are arranged around each other and never clash).
        Two fixed tasks conflict when their [start, start+duration) windows
        overlap -- whether they belong to the same pet or different pets.
        Returns a list of human-readable warnings; never raises.
        """
        fixed = [
            t
            for t in tasks
            if t.is_due(day) and not t.completed and t.is_fixed()
        ]
        windows = [
            (
                t,
                TimeWindow(
                    t.fixed_start,
                    _to_time(_to_minutes(t.fixed_start) + t.duration_minutes),
                ),
            )
            for t in fixed
        ]

        warnings: list[str] = []
        for i, (task_a, win_a) in enumerate(windows):
            for task_b, win_b in windows[i + 1:]:
                if win_a.overlaps(win_b):
                    who_a = f"{task_a.pet_name}'s " if task_a.pet_name else ""
                    who_b = f"{task_b.pet_name}'s " if task_b.pet_name else ""
                    warnings.append(
                        f"Time conflict: {who_a}{task_a.title} "
                        f"({win_a.start:%H:%M}-{win_a.end:%H:%M}) overlaps "
                        f"{who_b}{task_b.title} "
                        f"({win_b.start:%H:%M}-{win_b.end:%H:%M})."
                    )
        return warnings

    def _place_fixed(self, task: Task, timeline: Timeline) -> ScheduledTask | None:
        """Place a fixed-time `task` at its exact start, if the slot is free."""
        start = _to_minutes(task.fixed_start)
        end = start + task.duration_minutes
        window = TimeWindow(_to_time(start), _to_time(end))

        within_day = (
            start >= _to_minutes(timeline.day_start)
            and end <= _to_minutes(timeline.day_end)
        )
        if not within_day or any(window.overlaps(b) for b in timeline.busy):
            return None

        timeline.reserve(window)
        return ScheduledTask(
            task=task,
            start=window.start,
            end=window.end,
            reason=f"Fixed time - must occur at {task.fixed_start:%H:%M}.",
        )

    def _place(self, task: Task, timeline: Timeline) -> ScheduledTask | None:
        """Place a flexible `task`, honoring its soft preferred window."""
        slot = timeline.find_slot(task.duration_minutes, task.preferred_window)
        if slot is None:
            return None

        timeline.reserve(slot)
        prio = task.priority.name.capitalize()
        if task.preferred_window is None:
            reason = f"{prio} priority - placed in the first open slot."
        elif self._within(slot, task.preferred_window):
            reason = f"{prio} priority - placed within its preferred window."
        else:
            reason = (
                f"{prio} priority - preferred window was full, "
                "placed in the next open slot."
            )
        return ScheduledTask(task=task, start=slot.start, end=slot.end, reason=reason)

    @staticmethod
    def _within(inner: TimeWindow, outer: TimeWindow) -> bool:
        """Return True if `inner` lies fully inside `outer`."""
        return _to_minutes(outer.start) <= _to_minutes(inner.start) and _to_minutes(
            inner.end
        ) <= _to_minutes(outer.end)
