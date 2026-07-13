"""PawPal+ core package.

Backend logic lives in `pawpal.pawpal_system`. Re-exported here so callers can
`from pawpal import Task, Scheduler, ...`.
"""

from .pawpal_system import (
    Owner,
    Pet,
    Plan,
    Preferences,
    Priority,
    Recurrence,
    Scheduler,
    ScheduledTask,
    Task,
    TaskType,
    TimeWindow,
)

__all__ = [
    "Owner",
    "Pet",
    "Plan",
    "Preferences",
    "Priority",
    "Recurrence",
    "Scheduler",
    "ScheduledTask",
    "Task",
    "TaskType",
    "TimeWindow",
]
