# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

PawPal+ turns a list of care tasks into an explainable daily plan. The
scheduling algorithms it implements:

- **Priority sorting** — tasks are ordered highest-priority first, with shorter
  tasks breaking ties so more of the day gets used (`Scheduler.sort_tasks`).
- **Chronological schedule output** — the generated plan is returned in
  start-time order, regardless of the order tasks were entered.
- **Fixed-time placement** — tasks with a required time (e.g. meds at 08:00)
  claim their exact slot first; everything else flows around them.
- **Soft preferred windows** — a task can prefer a window (e.g. "morning walk");
  the scheduler honors it when possible and relaxes it when the day is full.
- **Blocked-time awareness** — periods the owner is unavailable (e.g. work hours)
  are never scheduled over.
- **No double-booking** — a free/busy timeline guarantees placed tasks never
  overlap.
- **Conflict warnings** — two tasks demanding the same fixed time are flagged
  with a plain-English warning instead of crashing (`Scheduler.detect_conflicts`).
- **Daily / weekly / one-off recurrence** — tasks can repeat daily, on a chosen
  weekday, or happen once on a date (`Task.is_due`).
- **Auto-regenerating recurring tasks** — completing a daily/weekly task
  automatically creates its next occurrence for the following day/week
  (`Pet.complete_task` → `Task.next_occurrence`).
- **Filtering** — view tasks by pet and/or completion status
  (`Owner.filter_tasks`).
- **Explainable plans** — every scheduled task carries a reason, and skipped
  tasks say why they were dropped.
- **Multi-pet households** — one owner can manage several pets; the plan
  aggregates and labels tasks across all of them.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Terminal output from running the demo script (`python main.py`), which builds an
owner (Jordan) with two pets (Leo the dog, Luna the cat) and schedules their care
tasks for the day. The owner is free 07:00–21:00 but blocked for work 09:00–17:00.

```
============================================================
Today's Schedule for Jordan
============================================================
Daily plan for 2026-07-12:
  07:00-07:10  Luna's Feeding (10 min) [high] - High priority - placed in the first open slot.
  07:10-07:40  Leo's Morning walk (30 min) [high] - High priority - placed within its preferred window.
  07:40-07:55  Luna's Weekly brush (15 min) [medium] - Medium priority - placed in the first open slot.
  08:00-08:10  Leo's Meds (10 min) [high] - Fixed time - must occur at 08:00.
  08:10-08:30  Luna's Playtime (20 min) [low] - Low priority - placed in the first open slot.
  17:00-17:30  Leo's Evening walk (30 min) [medium] - Medium priority - placed within its preferred window.
------------------------------------------------------------
Total scheduled time: 115 minutes
```

Notice how the plan respects the constraints: the fixed-time **Meds** task lands
exactly at 08:00 and the flexible tasks flow around it; nothing is scheduled
during the 09:00–17:00 work block, so the **Evening walk** waits until 17:00; and
each line explains *why* the task was placed there.

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest

# Or with coverage:
python -m pytest --cov=pawpal
```

The suite (`tests/test_pawpal.py`, 48 tests) covers:

- **Time helpers** — `TimeWindow.contains` / `overlaps` / `duration_minutes` (half-open ranges; touching edges don't overlap).
- **Task model** — recurrence due-logic (daily/weekly/once), the `not_before` guard, completion toggling, and `is_fixed`.
- **Sorting** — `Scheduler.sort_tasks` orders by priority then duration; the generated plan comes out in chronological order.
- **Filtering** — `Owner.filter_tasks` by pet name, completion status, both, or neither.
- **Recurrence regeneration** — completing a daily/weekly task spawns its next occurrence (and one-off tasks don't repeat); a completed daily task is not re-scheduled the same day.
- **Scheduling** — fixed-time placement, blocked windows and day bounds respected, soft preferred windows, tasks that don't fit are skipped, and the no-overlap invariant.
- **Conflict detection** — duplicate/overlapping fixed times are flagged as warnings without crashing.

Successful test run:

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\titi0\OneDrive\Documents\VSC\AI_110\Week_4\pawpal-starter-main
plugins: anyio-4.13.0
collected 48 items

tests\test_pawpal.py ................................................    [100%]

============================= 48 passed in 0.05s ==============================
```

### Confidence Level: ★★★★☆ (4 / 5)

All 48 tests pass, covering every core behavior plus important edge cases (fixed-time
bounds, blocked windows, the no-overlap invariant, recurrence boundaries, and
cross-pet conflicts). I hold back the fifth star because a few edges are documented
but not yet tested — notably input validation (zero/negative task durations) and
fragmented free time (a task larger than any single gap but smaller than the total
remaining time). The logic is reliable for realistic use; these are the areas I'd
harden next.

## 📐 Smarter Scheduling

Beyond placing tasks on a timeline, PawPal+ implements several "smarter"
behaviors. Each is documented below with the method that implements it (all in
`pawpal/pawpal_system.py`).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_tasks()` | Orders tasks by priority (highest first), then shorter duration first as a tie-breaker. Used internally by `build_plan` and available on its own. |
| Filtering | `Owner.filter_tasks(pet_name, completed)` | Returns tasks across all pets, filtered by pet name and/or completion status. Passing `None` for a field skips that filter. |
| Conflict detection | `Scheduler.detect_conflicts()` | Lightweight pairwise check over fixed-time tasks (same or different pets). Returns human-readable warning strings and never raises; results are also stored on `Plan.warnings`. |
| Recurring tasks | `Task.is_due()`, `Task.next_occurrence()`, `Pet.complete_task()` | `is_due` decides whether a daily/weekly/once task applies on a given day. Completing a recurring task via `complete_task` auto-creates its next occurrence (`next_occurrence`), stamped with a `not_before` date so it isn't re-scheduled the same day. |
| Fixed vs. flexible placement | `Scheduler._place_fixed()`, `Scheduler._place()` | Fixed-time tasks claim their exact slot first; flexible tasks fill the gaps, honoring a preferred window as a *soft* preference. |
| Free/busy time model | `Timeline.free_intervals()`, `Timeline.find_slot()`, `Timeline.reserve()` | Tracks open vs. occupied time so tasks never overlap and blocked periods (e.g. work hours) are respected. |

### Feature details

- **Sorting behavior — `Scheduler.sort_tasks(tasks)`**
  A static method that sorts by `(-priority.weight, duration_minutes)`: higher
  priority wins, and among equal priorities the shorter task goes first so more
  tasks fit.

- **Filtering behavior — `Owner.filter_tasks(pet_name=None, completed=None)`**
  Filter the household's tasks by pet (`pet_name="Leo"`) and/or by completion
  status (`completed=False` for pending, `True` for done). Both are optional.

- **Conflict detection — `Scheduler.detect_conflicts(tasks, day)`**
  Only fixed-time tasks can truly clash (flexible tasks are arranged around each
  other). It compares each pair's `[start, start+duration)` window and returns a
  warning for every overlap, e.g.
  `Time conflict: Leo's Meds (08:00-08:10) overlaps Luna's Insulin (08:00-08:10).`

- **Recurring task logic — `Task.is_due()` / `Task.next_occurrence()` / `Pet.complete_task()`**
  Tasks recur `DAILY`, `WEEKLY` (anchored to a weekday), or `ONCE` (anchored to a
  date). Marking a recurring task complete spawns the next occurrence (+1 day or
  +7 days) with a `not_before` guard so today's finished walk rolls to tomorrow
  instead of reappearing today.

## 📸 Demo Walkthrough

### Running the app

```bash
streamlit run app.py
```

### What the UI lets you do

The Streamlit app is organized top-to-bottom:

- **Owner & day preferences** — set the owner's name, the day's start/end times,
  and optionally block a work period (nothing is scheduled during it).
- **Pets** — add one or more pets (name + species). New pets appear immediately
  because the owner is persisted in `st.session_state`.
- **Add a care task** — pick which pet the task is for, then enter a title,
  duration, priority, and type. Optionally mark it as a **fixed-time** task or
  give it a **preferred window**.
- **Current tasks** — a table of tasks, **filtered** (one pet or all pets) and
  **sorted by priority**. A checkbox toggles the household-wide view.
- **Today's schedule** — the **Generate schedule** button builds the plan and
  displays it as a table, with a green success banner, any conflict warnings,
  and a list of skipped tasks with reasons.

### Example workflow

1. Set the day window to **07:00–21:00** and block **09:00–17:00** for work.
2. Add a pet: **Leo** (dog). Add another: **Luna** (cat).
3. For Leo, add **"Morning walk"** (30 min, high) with a preferred window of
   07:00–09:00, and **"Meds"** (10 min, high) fixed at **08:00**.
4. For Luna, add **"Feeding"** (10 min, high) and **"Insulin"** (10 min) also
   fixed at **08:00** — deliberately clashing with Leo's Meds.
5. Click **Generate schedule** and read the plan.

### Key scheduler behaviors shown

- **Priority sorting** — high-priority tasks (Feeding, Morning walk) are placed
  before lower-priority ones.
- **Fixed-time placement** — Meds lands exactly at 08:00; flexible tasks flow
  around it.
- **Blocked time respected** — nothing is scheduled during 09:00–17:00.
- **Conflict warning** — Leo's Meds and Luna's Insulin both want 08:00, so a
  ⚠️ warning appears and one is skipped (the app keeps running).
- **Explainability** — each row shows *why* the task landed where it did.

### Sample CLI output (`python main.py`)

The demo script exercises the sorting, filtering, conflict-detection, and
scheduling logic in the terminal:

```
============================================================
PawPal+ demo for Jordan
============================================================

All tasks (insertion order):
  [done]   Leo: Evening walk   low     30 min
  [todo]   Leo: Morning walk   high    30 min
  [todo]   Leo: Brush coat     medium  15 min
  [todo]   Leo: Meds           high    10 min
  [done]  Luna: Playtime       low     20 min
  [todo]  Luna: Feeding        high    10 min
  [todo]  Luna: Insulin        high    10 min

Pending only (filter completed=False):
  [todo]   Leo: Morning walk   high    30 min
  [todo]   Leo: Brush coat     medium  15 min
  [todo]   Leo: Meds           high    10 min
  [todo]  Luna: Feeding        high    10 min
  [todo]  Luna: Insulin        high    10 min

Completed only (filter completed=True):
  [done]   Leo: Evening walk   low     30 min
  [done]  Luna: Playtime       low     20 min

Leo's tasks only (filter pet_name='Leo'):
  [done]   Leo: Evening walk   low     30 min
  [todo]   Leo: Morning walk   high    30 min
  [todo]   Leo: Brush coat     medium  15 min
  [todo]   Leo: Meds           high    10 min

Pending tasks sorted by priority (Scheduler.sort_tasks):
  [todo]   Leo: Meds           high    10 min
  [todo]  Luna: Feeding        high    10 min
  [todo]  Luna: Insulin        high    10 min
  [todo]   Leo: Morning walk   high    30 min
  [todo]   Leo: Brush coat     medium  15 min

Conflict check (Scheduler.detect_conflicts):
  ! Time conflict: Leo's Meds (08:00-08:10) overlaps Luna's Insulin (08:00-08:10).

============================================================
Today's Schedule
============================================================
Daily plan for 2026-07-12:
  07:00-07:10  Luna's Feeding (10 min) [high] - High priority - placed in the first open slot.
  07:10-07:40  Leo's Morning walk (30 min) [high] - High priority - placed in the first open slot.
  07:40-07:55  Leo's Brush coat (15 min) [medium] - Medium priority - placed in the first open slot.
  08:00-08:10  Leo's Meds (10 min) [high] - Fixed time - must occur at 08:00.
Skipped:
  Luna's Insulin (10 min) - Fixed time 08:00 does not fit (outside the day or conflicts with another commitment).
Warnings:
  ! Time conflict: Leo's Meds (08:00-08:10) overlaps Luna's Insulin (08:00-08:10).
------------------------------------------------------------
Total scheduled time: 65 minutes
```
