# PawPal+ — UML Class Diagram

Class diagram reflecting the implementation in `pawpal/pawpal_system.py`.

```mermaid
classDiagram
    class Priority {
        <<enum>>
        LOW
        MEDIUM
        HIGH
        +weight() int
    }

    class TaskType {
        <<enum>>
        WALK
        FEEDING
        MEDICATION
        GROOMING
        ENRICHMENT
        OTHER
    }

    class Recurrence {
        <<enum>>
        ONCE
        DAILY
        WEEKLY
    }

    class TimeWindow {
        +time start
        +time end
        +contains(t) bool
        +overlaps(other) bool
        +duration_minutes() int
    }

    class Preferences {
        +time day_start
        +time day_end
        +list~TimeWindow~ blocked_windows
        +is_blocked(window) bool
    }

    class Task {
        +str title
        +int duration_minutes
        +str pet_name
        +Priority priority
        +TaskType task_type
        +TimeWindow preferred_window
        +time fixed_start
        +Recurrence recurrence
        +date due_date
        +int weekday
        +bool completed
        +is_due(day) bool
        +is_fixed() bool
        +mark_complete() void
        +reset() void
    }

    class Pet {
        +str name
        +str species
        +str breed
        +int age
        +list~Task~ tasks
        +add_task(task) Task
        +remove_task(task) void
    }

    class Owner {
        +str name
        +Preferences preferences
        +list~Pet~ pets
        +add_pet(pet) Pet
        +all_tasks() list~Task~
    }

    class ScheduledTask {
        +Task task
        +time start
        +time end
        +str reason
    }

    class Plan {
        +date day
        +list~ScheduledTask~ scheduled
        +list~tuple~ skipped
        +total_minutes() int
        +summary() str
    }

    class Timeline {
        +time day_start
        +time day_end
        +list~TimeWindow~ busy
        +free_intervals() list~TimeWindow~
        +find_slot(duration_minutes, preferred) TimeWindow
        +reserve(window) void
    }

    class Scheduler {
        +Preferences preferences
        +plan_for_owner(owner, day) Plan
        +build_plan(tasks, day) Plan
        -_due_tasks(tasks, day) list
        -_build_timeline(day) Timeline
        -_sort_tasks(tasks) list
        -_place_fixed(task, timeline) ScheduledTask
        -_place(task, timeline) ScheduledTask
        -_within(inner, outer) bool
    }

    Owner "1" --> "1" Preferences : has
    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : has tasks
    Preferences "1" --> "*" TimeWindow : blocked_windows
    Task "1" --> "1" Priority
    Task "1" --> "1" TaskType
    Task "1" --> "1" Recurrence
    Task "0..1" --> "1" TimeWindow : preferred_window
    ScheduledTask "1" --> "1" Task : wraps
    Plan "1" --> "*" ScheduledTask : scheduled
    Plan "1" --> "*" Task : skipped
    Scheduler "1" --> "1" Preferences : uses
    Scheduler ..> Timeline : builds
    Scheduler ..> Plan : produces
    Timeline "1" --> "*" TimeWindow : busy / free
```
