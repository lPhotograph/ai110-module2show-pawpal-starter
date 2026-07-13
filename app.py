from datetime import date, time

import streamlit as st

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

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pet's care day around your time, priorities, and preferences.")

# ---------------------------------------------------------------------------
# Session state: create the Owner ONCE and reuse it across reruns.
#
# Streamlit re-runs this script top-to-bottom on every interaction, so a plain
# `owner = Owner(...)` would be recreated empty each time. Storing it in
# st.session_state (the per-session "vault") keeps the pets and tasks we add.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="",
        preferences=Preferences(day_start=time(7, 0), day_end=time(21, 0)),
        # Start with no pets -- the user adds their own below.
        pets=[],
    )

owner = st.session_state.owner  # the SAME instance every rerun

# ---------------------------------------------------------------------------
# Owner & day preferences
# ---------------------------------------------------------------------------
with st.expander("Owner & day preferences", expanded=True):
    owner.name = st.text_input("Owner name", value=owner.name, placeholder="e.g. Jordan")

    c1, c2 = st.columns(2)
    owner.preferences.day_start = c1.time_input(
        "Day starts", value=owner.preferences.day_start
    )
    owner.preferences.day_end = c2.time_input(
        "Day ends", value=owner.preferences.day_end
    )

    has_work = st.checkbox(
        "Block a work period (nothing scheduled then)",
        value=bool(owner.preferences.blocked_windows),
    )
    if has_work:
        w1, w2 = st.columns(2)
        work_start = w1.time_input("Work starts", value=time(9, 0), key="work_start")
        work_end = w2.time_input("Work ends", value=time(17, 0), key="work_end")
        owner.preferences.blocked_windows = [TimeWindow(work_start, work_end)]
    else:
        owner.preferences.blocked_windows = []

# ---------------------------------------------------------------------------
# Pets: add new pets (Owner.add_pet) and pick which one to plan for
# ---------------------------------------------------------------------------
with st.expander("Pets", expanded=True):
    # Add-a-pet form. On submit, Owner.add_pet handles the data; because `owner`
    # is persisted in session_state, the new pet survives the rerun and shows up
    # in the selector below.
    with st.form("add_pet", clear_on_submit=True):
        st.markdown("**Add a pet**")
        f1, f2 = st.columns(2)
        new_pet_name = f1.text_input("Name")
        new_pet_species = f2.selectbox("Species", ["dog", "cat", "other"])
        submitted = st.form_submit_button("Add pet")

    if submitted:
        if new_pet_name.strip():
            owner.add_pet(Pet(name=new_pet_name.strip(), species=new_pet_species))
            st.success(f"Added {new_pet_name.strip()} to {owner.name}'s pets.")
        else:
            st.warning("Please enter a name for the pet.")

# Nothing else makes sense until there's at least one pet, so stop here.
if not owner.pets:
    st.info("👆 Add a pet to start planning care tasks.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Add tasks (built as real Task objects and stored on the selected pet)
# ---------------------------------------------------------------------------
st.subheader("Add a care task")

# Choose which pet this task is for (tasks are added to this one).
active = st.selectbox(
    "For which pet?",
    options=range(len(owner.pets)),
    format_func=lambda i: f"{owner.pets[i].name} ({owner.pets[i].species})",
)
pet = owner.pets[active]

task_title = st.text_input("Task title", value="Morning walk", key="task_title")

c1, c2, c3 = st.columns(3)
duration = c1.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
priority_label = c2.selectbox("Priority", ["low", "medium", "high"], index=2)
type_label = c3.selectbox("Type", [t.value for t in TaskType])

# Optional timing constraints.
use_fixed = st.checkbox("Must happen at a fixed time")
fixed_start = None
if use_fixed:
    fixed_start = st.time_input("Fixed start time", value=time(8, 0), key="fixed_start")

use_pref = st.checkbox("Has a preferred time window (soft)")
preferred_window = None
if use_pref:
    p1, p2 = st.columns(2)
    pref_start = p1.time_input("Prefer after", value=time(7, 0), key="pref_start")
    pref_end = p2.time_input("Prefer before", value=time(9, 0), key="pref_end")
    preferred_window = TimeWindow(pref_start, pref_end)

if st.button("Add task"):
    pet.add_task(
        Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority[priority_label.upper()],
            task_type=TaskType(type_label),
            fixed_start=fixed_start,
            preferred_window=preferred_window,
        )
    )
    st.success(f"Added “{task_title}” for {pet.name}.")

# ---------------------------------------------------------------------------
# Current tasks
# ---------------------------------------------------------------------------
st.subheader(f"Current tasks for {pet.name}")
if pet.tasks:
    rows = []
    for t in pet.tasks:
        if t.is_fixed():
            when = f"fixed {t.fixed_start:%H:%M}"
        elif t.preferred_window is not None:
            when = (
                f"prefers {t.preferred_window.start:%H:%M}"
                f"–{t.preferred_window.end:%H:%M}"
            )
        else:
            when = "flexible"
        rows.append(
            {
                "Task": t.title,
                "Min": t.duration_minutes,
                "Priority": t.priority.name.lower(),
                "Type": t.task_type.value,
                "When": when,
                "Done": t.completed,
            }
        )
    st.table(rows)

    if st.button("Clear all tasks"):
        pet.tasks.clear()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Generate the schedule
# ---------------------------------------------------------------------------
st.subheader("Today's schedule")

if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner.preferences)
    plan = scheduler.plan_for_owner(owner, date.today())

    st.markdown(f"**Plan for {owner.name} — {date.today():%A, %B %d, %Y}**")

    if plan.scheduled:
        for item in plan.scheduled:
            t = item.task
            st.markdown(
                f"- **{item.start:%H:%M}–{item.end:%H:%M}** · "
                f"{t.pet_name}'s {t.title} ({t.duration_minutes} min) "
                f"`[{t.priority.name.lower()}]`  \n"
                f"  _{item.reason}_"
            )
        st.caption(f"Total scheduled time: {plan.total_minutes} minutes")
    else:
        st.info("Nothing could be scheduled for today.")

    if plan.skipped:
        st.markdown("**Skipped**")
        for task, why in plan.skipped:
            st.markdown(f"- {task.title} ({task.duration_minutes} min) — {why}")

    with st.expander("Plain-text plan (copy/paste)"):
        st.code(plan.summary(), language="text")