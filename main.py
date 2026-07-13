"""Temporary testing ground for PawPal+.

Run it from the project root to see the scheduler work end-to-end in the
terminal:

    python main.py

This is a scratch/demo script (not the app and not the test suite) -- it just
wires a small household together and prints the generated plan so we can eyeball
the logic.
"""

from datetime import date, time

from pawpal.pawpal_system import (
    Owner,
    Pet,
    Preferences,
    Priority,
    Recurrence,
    Scheduler,
    Task,
    TaskType,
    TimeWindow,
)


def build_household() -> Owner:
    """Create one owner, two pets, and a handful of care tasks."""
    # The owner is free 07:00-21:00 but busy at work 09:00-17:00.
    prefs = Preferences(
        day_start=time(7, 0),
        day_end=time(21, 0),
        blocked_windows=[TimeWindow(time(9, 0), time(17, 0))],
    )
    owner = Owner(name="Jordan", preferences=prefs)

    # --- Pet 1: Leo the dog ---------------------------------------------
    leo = owner.add_pet(Pet(name="Leo", species="dog", breed="Corgi", age=3))
    leo.add_task(
        Task(
            "Morning walk",
            duration_minutes=30,
            priority=Priority.HIGH,
            task_type=TaskType.WALK,
            preferred_window=TimeWindow(time(7, 0), time(9, 0)),  # before work
        )
    )
    leo.add_task(
        Task(
            "Meds",
            duration_minutes=10,
            priority=Priority.HIGH,
            task_type=TaskType.MEDICATION,
            fixed_start=time(8, 0),  # must happen at 08:00 sharp
        )
    )
    leo.add_task(
        Task(
            "Evening walk",
            duration_minutes=30,
            priority=Priority.MEDIUM,
            task_type=TaskType.WALK,
            preferred_window=TimeWindow(time(17, 0), time(20, 0)),  # after work
        )
    )

    # --- Pet 2: Luna the cat --------------------------------------------
    luna = owner.add_pet(Pet(name="Luna", species="cat", breed="Tabby", age=5))
    luna.add_task(
        Task(
            "Feeding",
            duration_minutes=10,
            priority=Priority.HIGH,
            task_type=TaskType.FEEDING,
        )
    )
    luna.add_task(
        Task(
            "Playtime",
            duration_minutes=20,
            priority=Priority.LOW,
            task_type=TaskType.ENRICHMENT,
        )
    )
    luna.add_task(
        Task(
            "Weekly brush",
            duration_minutes=15,
            priority=Priority.MEDIUM,
            task_type=TaskType.GROOMING,
            recurrence=Recurrence.WEEKLY,
            weekday=6,  # Sundays only -- shows up only when today is Sunday
        )
    )

    return owner


def main() -> None:
    owner = build_household()
    today = date.today()

    scheduler = Scheduler(owner.preferences)
    plan = scheduler.plan_for_owner(owner, today)

    print("=" * 60)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 60)
    print(plan.summary())
    print("-" * 60)
    print(f"Total scheduled time: {plan.total_minutes} minutes")


if __name__ == "__main__":
    main()
