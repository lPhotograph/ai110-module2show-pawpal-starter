# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

PawPal+ is built around three things a pet owner should always be able to do:

1. **Set up their household — add an owner and their pet(s).** The user enters their own name and their availability/preferences (when the day starts and ends, how much free time they have, any blocked hours like work), then adds one or more pets with basic info (name, species, breed, age). This is the foundation everything else builds on: tasks belong to pets, and the schedule is shaped by the owner's preferences.

2. **Add and manage care tasks.** For each pet, the user can add a task describing what needs to happen (e.g. "morning walk"), how long it takes, how important it is (low/medium/high), what type it is (walk, feeding, medication, grooming, enrichment), and optionally when it should happen — either a preferred window ("in the morning") or a fixed time it must occur ("meds at 08:00"). They can also say how often it repeats (once, daily, weekly). Tasks can be edited or removed.

3. **Generate and view today's plan.** With one action, the user asks PawPal+ to build a schedule for the day. The scheduler looks at which tasks are due today, respects the hard constraints (fixed times, time budget, day boundaries), orders the rest by priority, and places each task that fits — honoring preferred windows when the day allows. The user then sees a clear, time-ordered plan for the day, along with an explanation of why each task landed where it did and why any tasks were skipped.

---

**a. Initial design**

- Briefly describe your initial UML design.

The design separates *data* classes from the *behavior* class (the scheduler), so the scheduling logic stays a pure, testable `tasks → Plan` function with no UI code in it.

- What classes did you include, and what responsibilities did you assign to each?

- **Owner** — holds owner name, their `Preferences`, and their pets.
- **Pet** — basic pet info (name, species, breed, age); tasks belong to a pet.
- **Preferences** — the owner's day-level constraints: day start/end, total available minutes, and blocked windows (e.g. work hours).
- **TimeWindow** — a start/end span; used for preferred slots and blocked periods.
- **Task** — *what* needs to happen: title, duration, priority, type, optional preferred window or fixed start, and recurrence. Does not know *when* it will run.
- **ScheduledTask** — a `Task` placed on the timeline at a concrete start/end, plus a `reason` explaining the placement.
- **Plan** — the scheduler's output for a day: the scheduled tasks, the skipped ones (with reasons), and a summary.
- **Scheduler** — the only behavior class: turns tasks + preferences into a `Plan`.
- Enums (**Priority**, **TaskType**, **Recurrence**) replace magic strings.



**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
