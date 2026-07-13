"""PawPal+ logic layer.

All backend classes live here, kept separate from the Streamlit UI (`app.py`)
so the scheduling logic stays a pure, testable `tasks -> Plan` transformation.

Two groups of classes:
  * Data classes  — what things *are*: Owner, Pet, Preferences, TimeWindow,
                     Task, ScheduledTask, Plan (plus the Priority / TaskType /
                     Recurrence enums).
  * Behavior      — Scheduler, which turns tasks + preferences into a Plan.

This is a STUBS file: attributes and method signatures are defined, but the
method bodies are intentionally left unimplemented (`raise NotImplementedError`).
Fill them in incrementally, smallest/leaf methods first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum


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
        raise NotImplementedError


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
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TimeWindow:
    """A span of time within a day, e.g. a preferred slot or a blocked period."""

    start: time
    end: time

    def contains(self, t: time) -> bool:
        """Return True if `t` falls within [start, end)."""
        raise NotImplementedError

    def overlaps(self, other: "TimeWindow") -> bool:
        """Return True if this window overlaps `other`."""
        raise NotImplementedError

    def duration_minutes(self) -> int:
        """Length of the window in minutes."""
        raise NotImplementedError


@dataclass
class Preferences:
    """Owner-level scheduling constraints for a day."""

    day_start: time = time(7, 0)
    day_end: time = time(22, 0)
    available_minutes: int = 240
    blocked_windows: list[TimeWindow] = field(default_factory=list)

    def is_blocked(self, window: TimeWindow) -> bool:
        """Return True if `window` overlaps any blocked window."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet that care tasks are performed for."""

    name: str
    species: str = "dog"
    breed: str = ""
    age: int | None = None


@dataclass
class Owner:
    """The pet owner and their scheduling preferences."""

    name: str
    preferences: Preferences = field(default_factory=Preferences)
    pets: list[Pet] = field(default_factory=list)


@dataclass
class Task:
    """A single care task to (maybe) place on the day's timeline.

    A Task describes *what needs to happen*; it does not know *when* it will
    happen. Placement is decided by the Scheduler, which produces a
    ScheduledTask.
    """

    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    task_type: TaskType = TaskType.OTHER
    preferred_window: TimeWindow | None = None
    fixed_start: time | None = None
    recurrence: Recurrence = Recurrence.DAILY

    def is_due(self, day: date) -> bool:
        """Return True if this task should be scheduled on `day`.

        Depends on `recurrence` (e.g. WEEKLY tasks are due on one weekday).
        """
        raise NotImplementedError

    def is_fixed(self) -> bool:
        """Return True if the task must start at a specific time."""
        raise NotImplementedError


@dataclass
class ScheduledTask:
    """A Task placed on the timeline at a concrete start/end time."""

    task: Task
    start: time
    end: time
    reason: str = ""  # why the scheduler placed it here — powers the explanation


@dataclass
class Plan:
    """The output of the scheduler for a single day."""

    day: date
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[Task, str]] = field(default_factory=list)  # (task, why skipped)

    @property
    def total_minutes(self) -> int:
        """Total minutes of scheduled tasks."""
        raise NotImplementedError

    def summary(self) -> str:
        """Human-readable summary of the plan (for CLI/Streamlit display)."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Behavior
# ---------------------------------------------------------------------------


class Scheduler:
    """Builds a daily Plan from tasks and owner preferences.

    v1 algorithm (greedy, explainable):
      1. Filter to tasks due on `day` (recurrence).
      2. Place all fixed-start tasks first (hard constraint).
      3. Sort the rest by (priority desc, duration asc).
      4. Walk the day's free slots; place each task that fits, honoring its
         preferred window as a *soft* preference (relax it if the day is full).
      5. Subtract from the time budget; record a `reason` for each placement.
      6. Anything that doesn't fit -> Plan.skipped with a reason.
    """

    def __init__(self, preferences: Preferences) -> None:
        self.preferences = preferences

    def build_plan(self, tasks: list[Task], day: date) -> Plan:
        """Produce a Plan for `day` from `tasks`. Main entry point."""
        raise NotImplementedError

    def _due_tasks(self, tasks: list[Task], day: date) -> list[Task]:
        """Filter to tasks that recur on `day`."""
        raise NotImplementedError

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order non-fixed tasks by priority (desc) then duration (asc)."""
        raise NotImplementedError

    def _fits(self, task: Task, remaining_minutes: int) -> bool:
        """Return True if `task` fits within the remaining time budget."""
        raise NotImplementedError

    def _place(self, task: Task, cursor: time, remaining_minutes: int) -> ScheduledTask:
        """Place `task` starting at/after `cursor`, honoring soft preferences.

        Returns a ScheduledTask with a `reason` explaining the placement.
        """
        raise NotImplementedError
