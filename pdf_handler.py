
from pypdf import PdfReader


def extract_pdf_text(uploaded_file):
    """Extract readable text and statistics from an uploaded PDF."""

    pdf_reader = PdfReader(uploaded_file)
    page_count = len(pdf_reader.pages)
    pdf_text = ""

    for page in pdf_reader.pages:
        text = page.extract_text()
        if text:
            pdf_text += text + "\n"

    character_count = len(pdf_text)
    word_count = len(pdf_text.split())
    file_size_mb = uploaded_file.size / (1024 * 1024)

    return {
        "pdf_text": pdf_text,
        "page_count": page_count,
        "character_count": character_count,
        "word_count": word_count,
        "file_size_mb": file_size_mb
    }
