
import streamlit as st
import requests
from ai_helpers import generate_ai_response


def display_chatbot(pdf_text, subject):
    """Display the AI lecture chatbot."""

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("5. 💬 AI Lecture Chatbot")

    if not pdf_text.strip():
        st.info("Upload a PDF with readable text before using the chatbot.")
        return

    st.write("Ask questions about your uploaded lecture notes.")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input(
        "Ask a question about your lecture..."
    )

    if user_question:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

        prompt = f"""
You are a careful AI Study Assistant that helps students
understand their lecture notes.

RULES:
1. Use the provided lecture notes as your main source.
2. Do not invent facts or pretend information appears in
   the notes when it does not.
3. If the notes do not contain enough information, say so.
4. Explain concepts in simple English.
5. Use short paragraphs and bullet points when helpful.
6. Label illustrative examples clearly.
7. Check that your explanation is logically consistent.
8. For comparisons, explain each concept before comparing.
9. Do not make unsupported claims.
10. Do not repeat the question unnecessarily.

Subject: {subject or "General"}

Uploaded lecture notes:
{pdf_text[:12000]}

Student's question:
{user_question}

Answer:
"""

        try:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = generate_ai_response(prompt)
                    st.markdown(answer)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer
            })

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to Ollama. "
                "Please make sure Ollama is running."
            )

        except requests.exceptions.Timeout:
            st.error(
                "The AI took too long to respond. "
                "Please try again."
            )

        except requests.exceptions.RequestException as error:
            st.error(f"Unable to get an answer: {error}")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
