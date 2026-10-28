
import streamlit as st
from pypdf.errors import PdfReadError

from pdf_handler import extract_pdf_text
from chatbot import display_chatbot

st.title("💬 AI Study Chatbot")
st.write("Ask questions about your study materials and documents.")

subject = st.text_input("Subject (optional)", key="chatbot_subject")

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    key="chatbot_pdf"
)

if uploaded_file is not None:
    try:
        pdf_data = extract_pdf_text(uploaded_file)
        pdf_text = pdf_data["pdf_text"]

        if pdf_text.strip():
            st.success("Study material loaded successfully.")
            display_chatbot(pdf_text, subject)
        else:
            st.warning(
                "No readable text found in this PDF. "
                "It may contain scanned pages."
            )

    except (PdfReadError, OSError, ValueError) as error:
        st.error(f"Unable to read the PDF: {error}")
