
import json

import streamlit as st

from ai_helpers import generate_ai_response


def generate_flashcards(pdf_text, subject="", number_of_cards=10):
    """Generate question-and-answer flashcards from study material."""

    # Limit input size to help the local model process it.
    study_text = pdf_text[:12000]

    topic = subject.strip() if subject.strip() else "General Study Material"

    prompt = f"""
You are an educational assistant creating useful study flashcards.

Subject: {topic}

Read the study material and create exactly {number_of_cards}
flashcards based only on information supported by the material.

Requirements:
- Each card must test one important concept or fact.
- Keep each question clear and concise.
- Give an accurate, concise answer.
- Do not invent facts that are not in the material.
- Avoid duplicate questions.
- Return valid JSON only, without Markdown code fences.

Use this exact JSON structure:
{{
    "flashcards": [
        {{
            "question": "A question about the material",
            "answer": "The correct answer"
        }}
    ]
}}

Study material:
{study_text}
"""

    response = generate_ai_response(
        prompt,
        timeout=300,
        json_mode=True,
    )

    result = json.loads(response)
    cards = result.get("flashcards", [])

    if not isinstance(cards, list):
        raise ValueError("The AI returned an invalid flashcard list.")

    cleaned_cards = []

    for card in cards:
        if not isinstance(card, dict):
            continue

        question = card.get("question", "")
        answer = card.get("answer", "")

        if (
            isinstance(question, str)
            and isinstance(answer, str)
            and question.strip()
            and answer.strip()
        ):
            cleaned_cards.append({
                "question": question.strip(),
                "answer": answer.strip(),
            })

    if not cleaned_cards:
        raise ValueError(
            "No valid flashcards were generated. Please try again."
        )

    return cleaned_cards[:number_of_cards]


def display_flashcards(pdf_text, subject=""):
    """Display generated flashcards with review controls."""

    st.subheader("🗂️ AI Flashcards")
    st.write(
        "Turn your study materials into question-and-answer cards "
        "and practise remembering key concepts."
    )

    number_of_cards = st.select_slider(
    "Number of flashcards",
    options=[5, 10, 15, 20],
    value=10,
    key="flashcard_count",
    )

    if st.button(
        "✨ Generate Flashcards",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner("Generating your flashcards with AI..."):
                cards = generate_flashcards(
                    pdf_text,
                    subject,
                    number_of_cards,
                )

            st.session_state["flashcard_deck"] = cards
            st.session_state["flashcard_index"] = 0
            st.session_state["flashcard_known"] = []
            st.session_state["flashcard_review"] = []

        except Exception as error:
            st.error(
                f"Unable to generate flashcards: {error}"
            )

    cards = st.session_state.get("flashcard_deck", [])

    if not cards:
        st.info(
            "Upload a PDF and click Generate Flashcards to get started."
        )
        return

    index = st.session_state.get("flashcard_index", 0)
    index = min(index, len(cards) - 1)
    card = cards[index]

    st.progress(
        (index + 1) / len(cards),
        text=f"Card {index + 1} of {len(cards)}",
    )

    if "flashcard_show_answer" not in st.session_state:
        st.session_state["flashcard_show_answer"] = False

    with st.container(border=True):
        st.caption("QUESTION")

        st.markdown(f"### {card['question']}")

        if st.session_state["flashcard_show_answer"]:
            st.divider()
            st.caption("ANSWER")
            st.write(card["answer"])
        else:
            st.write("Think of your answer, then reveal it.")

            if st.button(
                "👀 Reveal Answer",
                use_container_width=True,
            ):
                st.session_state["flashcard_show_answer"] = True
                st.rerun()

    if st.session_state["flashcard_show_answer"]:
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "❌ Review Again",
                use_container_width=True,
            ):
                if index not in st.session_state["flashcard_review"]:
                    st.session_state["flashcard_review"].append(index)

                if index in st.session_state["flashcard_known"]:
                    st.session_state["flashcard_known"].remove(index)

                st.session_state["flashcard_show_answer"] = False

                if index < len(cards) - 1:
                    st.session_state["flashcard_index"] = index + 1

                st.rerun()

        with col2:
            if st.button(
                "✅ I Know This",
                use_container_width=True,
            ):
                if index not in st.session_state["flashcard_known"]:
                    st.session_state["flashcard_known"].append(index)

                if index in st.session_state["flashcard_review"]:
                    st.session_state["flashcard_review"].remove(index)

                st.session_state["flashcard_show_answer"] = False

                if index < len(cards) - 1:
                    st.session_state["flashcard_index"] = index + 1

                st.rerun()

    col_prev, col_next = st.columns(2)

    with col_prev:
        if st.button(
            "⬅️ Previous",
            disabled=index == 0,
            use_container_width=True,
        ):
            st.session_state["flashcard_index"] = index - 1
            st.session_state["flashcard_show_answer"] = False
            st.rerun()

    with col_next:
        if st.button(
            "Next ➡️",
            disabled=index >= len(cards) - 1,
            use_container_width=True,
        ):
            st.session_state["flashcard_index"] = index + 1
            st.session_state["flashcard_show_answer"] = False
            st.rerun()

    known_count = len(st.session_state.get("flashcard_known", []))
    review_count = len(st.session_state.get("flashcard_review", []))

    st.divider()
    st.subheader("📊 Your Review Progress")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Cards", len(cards))
    col2.metric("Know It", known_count)
    col3.metric("Review Again", review_count)

    if known_count + review_count == len(cards):
        st.success("You've reviewed every flashcard in this deck!")

    if st.button(
        "🔄 Start Again",
        use_container_width=True,
    ):
        st.session_state["flashcard_index"] = 0
        st.session_state["flashcard_show_answer"] = False
        st.session_state["flashcard_known"] = []
        st.session_state["flashcard_review"] = []
        st.rerun()
