"""Temporary testing ground for PawPal+.

Run it from the project root to exercise the logic in the terminal:

    python main.py

This is a scratch/demo script (not the app and not the test suite). It adds
tasks in a deliberately jumbled order, then uses the sorting and filtering
methods to prove they reorganize the data correctly.
"""

from datetime import date, time

from pawpal.pawpal_system import (
    Owner,
    Pet,
    Preferences,
    Priority,
    Scheduler,
    Task,
    TaskType,
    TimeWindow,
)


def build_household() -> Owner:
    """Create one owner, two pets, and a jumbled set of care tasks."""
    # The owner is free 07:00-21:00 but busy at work 09:00-17:00.
    prefs = Preferences(
        day_start=time(7, 0),
        day_end=time(21, 0),
        blocked_windows=[TimeWindow(time(9, 0), time(17, 0))],
    )
    owner = Owner(name="Jordan", preferences=prefs)

    leo = owner.add_pet(Pet(name="Leo", species="dog", breed="Corgi", age=3))
    luna = owner.add_pet(Pet(name="Luna", species="cat", breed="Tabby", age=5))

    # Add tasks OUT OF ORDER on purpose: low priority first, high priority last,
    # durations jumbled -- so the sort has real work to do.
    leo.add_task(Task("Evening walk", 30, priority=Priority.LOW, task_type=TaskType.WALK))
    luna.add_task(Task("Playtime", 20, priority=Priority.LOW, task_type=TaskType.ENRICHMENT))
    leo.add_task(Task("Morning walk", 30, priority=Priority.HIGH, task_type=TaskType.WALK))
    luna.add_task(Task("Feeding", 10, priority=Priority.HIGH, task_type=TaskType.FEEDING))
    leo.add_task(Task("Brush coat", 15, priority=Priority.MEDIUM, task_type=TaskType.GROOMING))
    leo.add_task(Task("Meds", 10, priority=Priority.HIGH, task_type=TaskType.MEDICATION,
                      fixed_start=time(8, 0)))
    # Conflict on purpose: Luna's insulin is also fixed at 08:00, clashing with
    # Leo's Meds -- the scheduler should warn about the overlap.
    luna.add_task(Task("Insulin", 10, priority=Priority.HIGH, task_type=TaskType.MEDICATION,
                       fixed_start=time(8, 0)))

    # Mark a couple as already done to show the completion filter.
    leo.tasks[0].mark_complete()   # Evening walk
    luna.tasks[0].mark_complete()  # Playtime

    return owner


def show(title: str, tasks) -> None:
    """Print a labeled list of tasks (title, pet, priority, duration, status)."""
    print(f"\n{title}")
    if not tasks:
        print("  (none)")
        return
    for t in tasks:
        status = "done" if t.completed else "todo"
        print(
            f"  [{status}] {t.pet_name:>5}: {t.title:<14} "
            f"{t.priority.name.lower():<6} {t.duration_minutes:>3} min"
        )


def main() -> None:
    owner = build_household()

    print("=" * 60)
    print(f"PawPal+ demo for {owner.name}")
    print("=" * 60)

    # --- Filtering -------------------------------------------------------
    show("All tasks (insertion order):", owner.all_tasks())
    show("Pending only (filter completed=False):",
         owner.filter_tasks(completed=False))
    show("Completed only (filter completed=True):",
         owner.filter_tasks(completed=True))
    show("Leo's tasks only (filter pet_name='Leo'):",
         owner.filter_tasks(pet_name="Leo"))

    # --- Sorting ---------------------------------------------------------
    # Sort the still-pending tasks by priority (highest first), then duration.
    pending_sorted = Scheduler.sort_tasks(owner.filter_tasks(completed=False))
    show("Pending tasks sorted by priority (Scheduler.sort_tasks):",
         pending_sorted)

    # --- Conflict detection ---------------------------------------------
    scheduler = Scheduler(owner.preferences)
    today = date.today()
    conflicts = scheduler.detect_conflicts(owner.all_tasks(), today)
    show_conflicts = "\n".join(f"  ! {c}" for c in conflicts) or "  (none)"
    print("\nConflict check (Scheduler.detect_conflicts):")
    print(show_conflicts)

    # --- Scheduling ------------------------------------------------------
    plan = scheduler.plan_for_owner(owner, today)
    print("\n" + "=" * 60)
    print("Today's Schedule")
    print("=" * 60)
    print(plan.summary())
    print("-" * 60)
    print(f"Total scheduled time: {plan.total_minutes} minutes")


if __name__ == "__main__":
    main()