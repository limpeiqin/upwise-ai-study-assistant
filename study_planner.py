
import html
import json
from datetime import date, timedelta

import streamlit as st
from st_rsuite import date_picker, date_range_picker

from ai_helpers import generate_ai_response


# Each subject gets its own consistent color.
SUBJECT_COLORS = [
    "#60A5FA",  # Blue
    "#34D399",  # Green
    "#FBBF24",  # Amber
    "#C084FC",  # Purple
    "#FB7185",  # Pink
    "#22D3EE",  # Cyan
    "#FB923C",  # Orange
    "#A3E635",  # Lime
]


def generate_study_plan(subjects, start_date, end_date, hours_per_day):
    """Generate and validate a study timetable using Ollama."""

    subject_details = [
        {
            "name": subject["name"],
            "exam_date": subject["exam_date"].isoformat(),
            "difficulty": subject["difficulty"],
        }
        for subject in subjects
    ]

    prompt = f"""
You are a helpful AI study planning assistant.

Create a realistic study timetable for a student.

Study period: {start_date} to {end_date}
Maximum combined study time per day: {hours_per_day} hours

Subjects:
{json.dumps(subject_details, indent=2)}

Requirements:
- Schedule sessions only within the study period.
- Use only the supplied subject names.
- Prioritize difficult subjects and earlier exam dates.
- Include reasonable breaks between sessions.
- The combined duration of all sessions on any day must not
  exceed {hours_per_day} hours.
- Use practical and specific study tasks.
- Spread sessions across available days where appropriate.
- Return valid JSON only, without Markdown code fences.

Use this exact structure:
{{
  "schedule": [
    {{
      "date": "YYYY-MM-DD",
      "subject": "Subject name",
      "task": "Specific study task",
      "duration_hours": 1,
      "reason": "Why this task is scheduled"
    }}
  ]
}}
"""

    response = generate_ai_response(
        prompt,
        timeout=300,
        json_mode=True,
    )

    try:
        result = json.loads(response)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "The AI returned an invalid timetable. Please try again."
        ) from error

    if not isinstance(result, dict):
        raise ValueError("The AI returned an invalid timetable.")

    schedule = result.get("schedule", [])

    if not isinstance(schedule, list) or not schedule:
        raise ValueError(
            "The AI did not create a valid timetable. Please try again."
        )

    allowed_subjects = {
        subject["name"] for subject in subjects
    }
    valid_sessions = []

    for session in schedule:
        if not isinstance(session, dict):
            continue

        session_date = session.get("date")
        subject = session.get("subject")
        task = session.get("task")
        duration = session.get("duration_hours")
        reason = session.get("reason", "")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (session_date, subject, task)
        ):
            continue

        try:
            parsed_date = date.fromisoformat(session_date)
            duration = float(duration)
        except (ValueError, TypeError):
            continue

        subject = subject.strip()

        if not start_date <= parsed_date <= end_date:
            continue

        if subject not in allowed_subjects:
            continue

        if not 0 < duration <= hours_per_day:
            continue

        valid_sessions.append({
            "date": parsed_date.isoformat(),
            "subject": subject,
            "task": task.strip(),
            "duration_hours": duration,
            "reason": (
                reason.strip() if isinstance(reason, str) else ""
            ),
        })

    if not valid_sessions:
        raise ValueError(
            "No valid study sessions were generated. Please try again."
        )

    # Check combined study hours for each date.
    daily_totals = {}

    for session in valid_sessions:
        day = session["date"]
        daily_totals[day] = (
            daily_totals.get(day, 0)
            + session["duration_hours"]
        )

    overloaded_days = [
        day
        for day, hours in daily_totals.items()
        if hours > hours_per_day + 1e-9
    ]

    if overloaded_days:
        raise ValueError(
            "The AI scheduled too many study hours on one or more days. "
            "Please generate the plan again."
        )

    return sorted(
        valid_sessions,
        key=lambda item: (item["date"], item["subject"]),
    )


def update_completed_session(index):
    """Synchronize completed tasks with progress tracking."""

    completed = st.session_state.setdefault(
        "study_plan_completed", []
    )
    checkbox_key = f"planner_completed_{index}"

    if st.session_state.get(checkbox_key, False):
        if index not in completed:
            completed.append(index)
    elif index in completed:
        completed.remove(index)


def display_study_planner():
    """Display the AI Study Planner."""

    st.title("📅 AI Study Planner")

    st.write(
        "Plan your study sessions around your subjects, exams, "
        "and available time."
    )

    today = date.today()
    default_end = today + timedelta(days=7)

    with st.form("study_planner_form"):
        st.subheader("1. Your Study Period")

        start_date, end_date = date_range_picker(
            label="Select your study period",
            value=(today, default_end),
            format="dd MMM, yyyy",
            locale="en_US",
            min_date=today,
            key="planner_study_period",
        )

        hours_per_day = st.slider(
            "Maximum study hours per day",
            min_value=1,
            max_value=8,
            value=3,
            help=(
                "All study sessions on the same day are added together "
                "and must stay within this limit."
            ),
        )

        st.subheader("2. Your Subjects")

        subject_count = st.number_input(
            "Number of subjects",
            min_value=1,
            max_value=8,
            value=3,
            step=1,
        )

        subjects = []

        for index in range(int(subject_count)):
            st.markdown(f"**Subject {index + 1}**")

            subject_name = st.text_input(
                "Subject name",
                key=f"planner_subject_{index}",
                placeholder="e.g. Database Systems",
            )

            exam_date = date_picker(
                label="Exam date",
                value=end_date or default_end,
                format="dd MMM, yyyy",
                locale="en_US",
                min_date=start_date or today,
                max_date=end_date or default_end,
                key=f"planner_exam_date_{index}",
            )

            difficulty = st.selectbox(
                "Difficulty",
                ["Easy", "Medium", "Hard"],
                index=1,
                key=f"planner_difficulty_{index}",
            )

            subjects.append({
                "name": subject_name.strip(),
                "exam_date": exam_date,
                "difficulty": difficulty,
            })

        submitted = st.form_submit_button(
            "✨ Generate My Study Plan",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if start_date is None or end_date is None:
            st.error("Please select both dates for your study period.")

        elif end_date < start_date:
            st.error("The end date must be on or after the start date.")

        elif any(not subject["name"] for subject in subjects):
            st.error("Please enter a name for every subject.")

        elif any(subject["exam_date"] is None for subject in subjects):
            st.error("Please select an exam date for every subject.")

        elif any(
            subject["exam_date"] < start_date
            or subject["exam_date"] > end_date
            for subject in subjects
        ):
            st.error(
                "Every exam date must fall within your selected study period."
            )

        else:
            try:
                with st.spinner("Creating your personalized study plan..."):
                    schedule = generate_study_plan(
                        subjects,
                        start_date,
                        end_date,
                        hours_per_day,
                    )

                st.session_state["study_plan"] = schedule
                st.session_state["study_plan_completed"] = []
                st.session_state["study_plan_hours_per_day"] = (
                    hours_per_day
                )

                for key in list(st.session_state.keys()):
                    if key.startswith("planner_completed_"):
                        del st.session_state[key]

            except Exception as error:
                st.error(f"Unable to create the study plan: {error}")

    schedule = st.session_state.get("study_plan", [])

    if not schedule:
        st.info(
            "Enter your subjects and exam dates, select your study period, "
            "and generate your study plan."
        )
        return

    # Use the limit saved with the generated plan.
    plan_hours_per_day = st.session_state.get(
        "study_plan_hours_per_day",
        hours_per_day,
    )

    # Group sessions by date.
    sessions_by_day = {}

    for index, session in enumerate(schedule):
        day = session["date"]
        sessions_by_day.setdefault(day, []).append((index, session))

    daily_totals = {
        day: sum(
            session["duration_hours"]
            for _, session in day_sessions
        )
        for day, day_sessions in sessions_by_day.items()
    }

    total_hours = sum(
        session["duration_hours"] for session in schedule
    )

    completed = st.session_state.setdefault(
        "study_plan_completed", []
    )

    # Assign a stable color to each subject in the input order.
    subject_order = list(dict.fromkeys(
        subject["name"]
        for subject in subjects
        if subject["name"]
    ))

    subject_color_map = {
        name: SUBJECT_COLORS[index % len(SUBJECT_COLORS)]
        for index, name in enumerate(subject_order)
    }

    st.divider()
    st.subheader("3. Your Study Schedule")

    # Simple summary.
    col1, col2, col3 = st.columns(3)

    col1.metric("Study Sessions", len(schedule))
    col2.metric("Study Days", len(sessions_by_day))
    col3.metric("Total Study Hours", f"{total_hours:g} hrs")

    st.caption(
        f"Daily limit: {plan_hours_per_day} hours. "
        "Total study hours include all sessions across your study period."
    )

    # Daily tasks grouped by date.
    st.subheader("Your Daily Tasks")

    for day, day_sessions in sorted(sessions_by_day.items()):
        day_hours = daily_totals[day]

        with st.container(border=True):
            st.markdown(
                f"**📅 {day}** · {day_hours:g} of "
                f"{plan_hours_per_day} hours planned"
            )

            st.progress(
                min(day_hours / plan_hours_per_day, 1.0)
            )

            for index, session in day_sessions:
                st.divider()

                # Each subject gets its own color and larger text.
                subject_color = subject_color_map.get(
                    session["subject"],
                    SUBJECT_COLORS[0],
                )
                safe_subject = html.escape(session["subject"])

                st.markdown(
                    f"<span style='color: {subject_color}; "
                    f"font-size: 1.2rem; font-weight: 700;'>"
                    f"{safe_subject}</span>",
                    unsafe_allow_html=True,
                )

                st.write(session["task"])

                st.caption(
                    f"Duration: {session['duration_hours']:g} hour(s)"
                )

                if session["reason"]:
                    st.caption(f"Why: {session['reason']}")

                st.checkbox(
                    "Mark as completed",
                    value=index in completed,
                    key=f"planner_completed_{index}",
                    on_change=update_completed_session,
                    args=(index,),
                )

    # Overall progress.
    completed_count = len(completed)
    progress = completed_count / len(schedule)

    st.divider()
    st.subheader("4. Your Progress")

    st.progress(progress)

    st.write(
        f"Completed {completed_count} of {len(schedule)} study sessions "
        f"({progress * 100:.0f}%)."
    )

    if st.button("🗑️ Clear Study Plan"):
        st.session_state.pop("study_plan", None)
        st.session_state.pop("study_plan_completed", None)
        st.session_state.pop("study_plan_hours_per_day", None)

        for key in list(st.session_state.keys()):
            if key.startswith("planner_completed_"):
                del st.session_state[key]

        st.rerun()
