
import streamlit as st
from supabase_client import supabase
from datetime import datetime

st.title("📊 Quiz History")
st.caption("Track your progress and review previous quiz attempts.")

user = st.session_state.get("user")

if not user:
    st.warning("Please sign in to view your quiz history.")
    st.stop()

# Load quiz history
try:
    response = (
        supabase.table("quiz_history")
        .select("*")
        .eq("user_id", user.id)
        .order("id", desc=True)
        .execute()
    )
    history = response.data or []

except Exception as error:
    st.error(f"Could not load quiz history: {error}")
    st.stop()

# Empty state
if not history:
    st.info("No quiz attempts yet. Complete your first quiz to see your progress!")
    st.stop()

# Calculate performance
scores = [float(q.get("score") or 0) for q in history]
total_attempts = len(history)
average_score = sum(scores) / total_attempts
best_score = max(scores)

# Performance overview
st.subheader("📈 Performance Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Attempts", total_attempts)

with col2:
    st.metric("Average Score", f"{average_score:.1f}%")

with col3:
    st.metric("Best Score", f"{best_score:.1f}%")

st.divider()

# History heading and refresh button
header_col, button_col = st.columns([4, 1])

with header_col:
    st.subheader("📝 Previous Attempts")

with button_col:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Display quiz history cards
for index, quiz in enumerate(history, start=1):
    subject = quiz.get("subject") or "General"
    mode = (quiz.get("quiz_mode") or "regular").title()
    total = int(quiz.get("total_questions") or 0)
    correct = int(quiz.get("correct_answers") or 0)
    score = float(quiz.get("score") or 0)

    # Format completion date and time
    created_at = quiz.get("created_at")
    formatted_date = "Date unavailable"

    if created_at:
        try:
            quiz_date = datetime.fromisoformat(
                created_at.replace("Z", "+00:00")
            )
            formatted_date = quiz_date.astimezone().strftime(
                "%d %b %Y, %I:%M %p"
            )
        except (ValueError, TypeError):
            pass

    # Quiz card
    with st.container(border=True):
        title_col, score_col = st.columns([3, 1])

        with title_col:
            st.markdown(f"**{subject}**")
            st.caption(
                f"Attempt #{index} · {mode} mode"
            )
            st.caption(f"📅 {formatted_date}")

        with score_col:
            st.metric("Score", f"{score:.1f}%")

        st.progress(max(0.0, min(score / 100, 1.0)))

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.caption(f"✅ Correct answers: {correct}/{total}")

        with detail_col2:
            st.caption(f"📋 Total questions: {total}")
