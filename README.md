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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
