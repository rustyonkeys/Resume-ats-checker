import pdfplumber


class PDFTextExtractionService:
    """Extract raw text from resume PDFs."""

    def extract_text(self, pdf_path: str) -> str:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
