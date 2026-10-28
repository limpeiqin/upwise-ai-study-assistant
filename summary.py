
import streamlit as st
from ai_helpers import generate_ai_response


def display_summary(pdf_text, subject):
    """Generate, display, and download an AI summary."""

    if st.button("✨ Summarize My Notes", type="primary"):
        chunk_size = 5000
        chunks = [
            pdf_text[i:i + chunk_size]
            for i in range(0, len(pdf_text), chunk_size)
        ]

        summaries = []

        try:
            progress = st.progress(0)
            status = st.empty()

            for index, chunk in enumerate(chunks):
                status.write(
                    f"Summarizing section {index + 1} of {len(chunks)}..."
                )

                prompt = f"""
You are a helpful study assistant.
Subject: {subject or "General"}
Summarize these study notes in simple English.
Include the main ideas, important definitions,
and key facts. Do not invent information.

Study notes:
{chunk}
"""

                result = generate_ai_response(prompt)
                summaries.append(result)
                progress.progress((index + 1) / len(chunks))

            status.write("Preparing your final summary...")

            final_prompt = f"""
You are a helpful study assistant.
Subject: {subject or "General"}

Combine the following section summaries into
one clear, well-organized study summary in simple English.

Include:
1. Main ideas
2. Important definitions
3. Key points to remember
4. A short conclusion

Do not invent facts.

Section summaries:
{" ".join(summaries)}
"""

            st.session_state.summary = generate_ai_response(final_prompt)

            status.empty()
            progress.empty()

        except Exception as error:
            st.error(f"Unable to generate the summary: {error}")

    if st.session_state.get("summary"):
        st.subheader("📝 Your AI Summary")
        st.markdown(st.session_state.summary)

        st.download_button(
            "📥 Download Summary",
            data=st.session_state.summary,
            file_name="study_summary.txt",
            mime="text/plain",
            key="download_summary"
        )
