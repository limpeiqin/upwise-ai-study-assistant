
import json
import re
import requests
import streamlit as st

from ai_helpers import generate_ai_response


def normalize_topic(topic):
    """Normalize topic names so similar labels can be grouped."""
    if not isinstance(topic, str) or not topic.strip():
        return "general"

    cleaned = re.sub(
        r"\s*\(?\s*continued\s*\)?\s*$",
        "",
        topic.strip(),
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.casefold() or "general"


def display_topic_name(topic):
    """Return a readable topic name."""
    if not isinstance(topic, str) or not topic.strip():
        return "General"

    return re.sub(r"\s+", " ", topic).strip()


def generate_quiz_questions(
    pdf_text,
    subject,
    number_of_questions,
    weak_topics=None,
):
    """Generate, validate, and retry missing quiz questions."""

    weak_topics = weak_topics or []
    valid_questions = []
    seen_questions = set()
    max_attempts = 3

    for attempt in range(max_attempts):
        missing = number_of_questions - len(valid_questions)

        if missing <= 0:
            break

        if weak_topics:
            topic_instruction = (
                "Focus on these weak topics from the study material: "
                + ", ".join(weak_topics)
                + ". Generate new questions about these topics."
            )
        else:
            topic_instruction = (
                "Cover important concepts across the study material."
            )

        existing_questions = [
            question["question"] for question in valid_questions
        ]

        prompt = f"""
You are an educational assistant.

Create exactly {missing} quiz questions based ONLY on the study material.

Subject: {subject or "General"}

Instructions:
- {topic_instruction}
- Include multiple-choice and true/false questions.
- Multiple-choice questions must have four different options: A, B, C, D.
- True/false questions must use A for True and B for False.
- Include the correct answer and a short explanation.
- Give each question a short topic label.
- Use consistent topic labels for related concepts.
- Do not repeat these existing questions:
  {json.dumps(existing_questions)}
- Do not invent facts.
- Return valid JSON only, without Markdown code fences.
- Return exactly {missing} complete questions.

Use this JSON structure:
{{
  "questions": [
    {{
      "type": "multiple_choice",
      "topic": "Topic name",
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "answer": "A",
      "explanation": "Explanation"
    }},
    {{
      "type": "true_false",
      "topic": "Topic name",
      "question": "Statement",
      "options": {{
        "A": "True",
        "B": "False"
      }},
      "answer": "A",
      "explanation": "Explanation"
    }}
  ]
}}

Study material:
{pdf_text[:10000]}
"""

        try:
            response = generate_ai_response(
                prompt,
                timeout=300,
                json_mode=True,
            )

            parsed = json.loads(response)
            questions = parsed.get("questions", [])

            if not isinstance(questions, list):
                continue

            for question in questions:
                if not isinstance(question, dict):
                    continue

                question_type = question.get("type")
                question_text = question.get("question")
                options = question.get("options")
                answer = question.get("answer")
                explanation = question.get("explanation", "")
                topic = question.get("topic", "General")

                if question_type not in (
                    "multiple_choice",
                    "true_false",
                ):
                    continue

                if (
                    not isinstance(question_text, str)
                    or not question_text.strip()
                ):
                    continue

                if (
                    not isinstance(options, dict)
                    or not isinstance(answer, str)
                ):
                    continue

                if not all(
                    isinstance(key, str)
                    and isinstance(value, str)
                    and value.strip()
                    for key, value in options.items()
                ):
                    continue

                if question_type == "multiple_choice":
                    if not all(
                        key in options for key in ("A", "B", "C", "D")
                    ):
                        continue

                    options = {
                        key: options[key]
                        for key in ("A", "B", "C", "D")
                    }

                else:
                    if not all(key in options for key in ("A", "B")):
                        continue

                    if (
                        options["A"].strip().casefold() != "true"
                        or options["B"].strip().casefold() != "false"
                    ):
                        continue

                    options = {
                        "A": options["A"],
                        "B": options["B"],
                    }

                option_texts = [
                    value.strip().casefold()
                    for value in options.values()
                ]

                if len(option_texts) != len(set(option_texts)):
                    continue

                if answer not in options:
                    continue

                question_text = question_text.strip()
                question_key = question_text.casefold()

                if question_key in seen_questions:
                    continue

                if not isinstance(explanation, str):
                    explanation = ""

                valid_questions.append({
                    "type": question_type,
                    "topic": display_topic_name(topic),
                    "question": question_text,
                    "options": options,
                    "answer": answer,
                    "explanation": explanation.strip(),
                })

                seen_questions.add(question_key)

                if len(valid_questions) >= number_of_questions:
                    break

        except (
            requests.exceptions.RequestException,
            json.JSONDecodeError,
            ValueError,
            KeyError,
            TypeError,
        ):
            # Try again if the AI response is invalid.
            continue

        if len(valid_questions) < number_of_questions:
            st.info(
                f"Collected {len(valid_questions)} of "
                f"{number_of_questions} valid questions. "
                f"Retrying to generate the missing questions "
                f"({attempt + 1}/{max_attempts})..."
            )

    if not valid_questions:
        raise ValueError(
            "The AI could not generate valid questions. "
            "Please try again."
        )

    return valid_questions[:number_of_questions]


def clear_quiz_state(clear_weak_topics=True):
    """Clear quiz answers and old radio selections."""

    old_questions = st.session_state.get("quiz_data") or []

    for index in range(len(old_questions)):
        key = f"quiz_question_{index}"
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.quiz_data = None
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False

    if clear_weak_topics:
        st.session_state.weak_topic_names = []


def display_quiz(pdf_text, subject):
    """Display quizzes, results, weak topics, and focused practice."""

    defaults = {
        "quiz_data": None,
        "quiz_answers": {},
        "quiz_submitted": False,
        "weak_topic_names": [],
        "quiz_mode": "regular",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.subheader("4. AI Quiz Generator")

    if not pdf_text.strip():
        st.info("Upload a PDF with readable text to generate a quiz.")
        return

    number_of_questions = st.selectbox(
        "Number of questions",
        [5, 10],
        index=0,
        key="quiz_number_of_questions",
    )

    if st.button("🧠 Generate Quiz", key="generate_regular_quiz"):
        clear_quiz_state()
        st.session_state.quiz_mode = "regular"

        try:
            with st.spinner("Generating your quiz..."):
                questions = generate_quiz_questions(
                    pdf_text,
                    subject,
                    number_of_questions,
                )

            st.session_state.quiz_data = questions

            st.success(f"Generated {len(questions)} valid questions.")

            if len(questions) < number_of_questions:
                st.warning(
                    f"You requested {number_of_questions} questions, "
                    f"but only {len(questions)} valid questions "
                    "could be generated after retries."
                )

            st.rerun()

        except (
            requests.exceptions.RequestException,
            json.JSONDecodeError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            st.error(f"Unable to generate a valid quiz: {error}")

    if not st.session_state.quiz_data:
        return

    questions = st.session_state.quiz_data

    st.markdown("### 📝 Answer Your Quiz")

    for index, question in enumerate(questions):
        st.markdown(
            f"**Question {index + 1}:** {question['question']}"
        )

        options = question["options"]

        selected = st.radio(
            "Choose your answer:",
            list(options.keys()),
            format_func=lambda choice, opts=options:
                f"{choice}. {opts[choice]}",
            key=f"quiz_question_{index}",
            index=None,
            disabled=st.session_state.quiz_submitted,
        )

        st.session_state.quiz_answers[index] = selected
        st.divider()

    if not st.session_state.quiz_submitted:
        if st.button("✅ Submit Quiz", key="submit_quiz"):
            st.session_state.quiz_submitted = True
            st.rerun()

    if not st.session_state.quiz_submitted:
        return

    correct_count = 0

    for index, question in enumerate(questions):
        user_answer = st.session_state.quiz_answers.get(index)
        correct_answer = question["answer"]
        options = question["options"]

        if user_answer == correct_answer:
            correct_count += 1
            st.success(f"Question {index + 1}: Correct!")
        else:
            st.error(
                f"Question {index + 1}: Incorrect. "
                f"Correct answer: {correct_answer}. "
                f"{options[correct_answer]}"
            )

        st.write(f"**Topic:** {question['topic']}")
        st.write(f"**Explanation:** {question['explanation']}")

    total = len(questions)
    score = correct_count / total * 100

    st.subheader("🏆 Your Quiz Results")
    st.metric("Score", f"{correct_count}/{total}")
    st.progress(score / 100)
    st.write(f"You scored **{score:.0f}%**.")

    # Analyse performance by topic.
    st.divider()
    st.subheader("🔍 AI Weak Topic Detector")

    st.write(
        "Topics below 60% accuracy are flagged for revision. "
        "Topics with fewer than three questions have limited evidence."
    )

    topic_results = {}

    for index, question in enumerate(questions):
        topic_name = display_topic_name(
            question.get("topic", "General")
        )
        topic_key = normalize_topic(topic_name)

        result = topic_results.setdefault(
            topic_key,
            {
                "name": topic_name,
                "correct": 0,
                "total": 0,
                "incorrect_questions": [],
            },
        )

        result["total"] += 1

        user_answer = st.session_state.quiz_answers.get(index)
        correct_answer = question["answer"]

        if user_answer == correct_answer:
            result["correct"] += 1
        else:
            result["incorrect_questions"].append({
                "question": question["question"],
                "correct_answer": correct_answer,
                "correct_text": question["options"][correct_answer],
            })

    weak_topics = []
    limited_evidence = []

    for topic_key, result in topic_results.items():
        accuracy = result["correct"] / result["total"] * 100

        st.markdown(f"**{result['name']}**")
        st.progress(accuracy / 100)
        st.caption(
            f"Accuracy: {accuracy:.0f}% "
            f"({result['correct']}/{result['total']} correct)"
        )

        if accuracy < 60:
            weak_topics.append(topic_key)

            if result["total"] < 3:
                limited_evidence.append(result["name"])

    # Display weak topics and incorrect-answer review.
    if weak_topics:
        st.warning("These topics may need more revision.")

        for topic_key in weak_topics:
            result = topic_results[topic_key]

            st.markdown(
                f"- **{result['name']}** — "
                f"{result['correct']}/{result['total']} correct"
            )

            if result["incorrect_questions"]:
                with st.expander(
                    f"Review incorrect questions: {result['name']}"
                ):
                    for item in result["incorrect_questions"]:
                        st.write(f"**Question:** {item['question']}")
                        st.write(
                            f"**Correct answer:** "
                            f"{item['correct_answer']}. "
                            f"{item['correct_text']}"
                        )

        if limited_evidence:
            st.info(
                "Limited evidence: "
                + ", ".join(limited_evidence)
                + ". These topics have fewer than three questions, "
                "so their accuracy may not reliably reflect "
                "your overall understanding."
            )

        st.session_state.weak_topic_names = [
            topic_results[key]["name"] for key in weak_topics
        ]

    else:
        st.success(
            "Great work! No weak topics were detected using "
            "the current 60% threshold."
        )
        st.session_state.weak_topic_names = []

    # Practice section is outside the weak-topic if/else.
    st.divider()
    st.subheader("🎯 Practice Weak Topics")

    if st.session_state.weak_topic_names:
        st.write(
            "Generate another quiz focused on the topics you answered "
            "incorrectly, using your uploaded study material."
        )

        if st.button(
            "🧠 Practise My Weak Topics",
            type="primary",
            key="practice_weak_topics_button",
        ):
            topics_to_practise = list(
                st.session_state.weak_topic_names
            )

            try:
                with st.spinner(
                    "Generating practice questions for your weak topics..."
                ):
                    practice_questions = generate_quiz_questions(
                        pdf_text,
                        subject,
                        number_of_questions,
                        weak_topics=topics_to_practise,
                    )

                clear_quiz_state(clear_weak_topics=False)
                st.session_state.quiz_data = practice_questions
                st.session_state.quiz_mode = "practice"

                st.success(
                    f"Generated {len(practice_questions)} practice "
                    "questions focused on your weak topics."
                )
                st.rerun()

            except (
                requests.exceptions.RequestException,
                json.JSONDecodeError,
                ValueError,
                KeyError,
                TypeError,
            ) as error:
                st.error(
                    f"Unable to generate focused practice questions: {error}"
                )
    else:
        st.info(
            "You have no detected weak topics in this quiz. "
            "Try another quiz or review the explanations above."
        )

    if st.button("🔄 Try Another Quiz", key="try_another_quiz"):
        clear_quiz_state()
        st.session_state.quiz_mode = "regular"
        st.rerun()
