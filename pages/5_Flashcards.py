
import streamlit as st
from pypdf.errors import PdfReadError

from pdf_handler import extract_pdf_text
from flashcards import display_flashcards


st.title("🗂️ AI Flashcard Generator")
st.write(
    "Turn your study materials into interactive flashcards "
    "to practise remembering key concepts."
)

subject = st.text_input(
    "Subject (optional)",
    key="flashcards_subject",
)

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    key="flashcards_pdf",
)

if uploaded_file is not None:
    try:
        pdf_data = extract_pdf_text(uploaded_file)
        pdf_text = pdf_data["pdf_text"]

        if pdf_text.strip():
            st.success(
                f"Extracted text from {pdf_data['page_count']} pages."
            )

            display_flashcards(pdf_text, subject)

        else:
            st.warning(
                "No readable text found in this PDF. "
                "It may contain scanned pages."
            )

    except (PdfReadError, OSError, ValueError) as error:
        st.error(f"Unable to read the PDF: {error}")
