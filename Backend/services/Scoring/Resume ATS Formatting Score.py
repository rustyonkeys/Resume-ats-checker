import fitz
import re


class ResumeFormatingScoring:

    def parsibility(
        self,
        pdf_path: str,
        resume_text: str,
        cleaned_text: str,
    ):
    