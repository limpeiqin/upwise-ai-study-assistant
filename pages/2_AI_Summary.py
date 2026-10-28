
import streamlit as st
from pypdf.errors import PdfReadError

from pdf_handler import extract_pdf_text
from summary import display_summary

st.title("📝 AI Summary")
st.write("Upload a study document to generate a concise summary.")

subject = st.text_input("Subject (optional)", key="summary_subject")

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    key="summary_pdf"
)

if uploaded_file is not None:
    try:
        pdf_data = extract_pdf_text(uploaded_file)
        pdf_text = pdf_data["pdf_text"]

        if pdf_text.strip():
            st.success(
                f"Extracted text from {pdf_data['page_count']} pages."
            )
            display_summary(pdf_text, subject)
        else:
            st.warning(
                "No readable text found in this PDF. "
                "It may contain scanned pages."
            )

    except (PdfReadError, OSError, ValueError) as error:
        st.error(f"Unable to read the PDF: {error}")
