import re
from typing import List, Tuple

import fitz


class ResumeFormatScoringService:
    """Detect ATS formatting risks in a resume PDF."""

    def check_format_issues(
        self,
        pdf_path: str,
        resume_text: str,
        cleaned_text: str,
    ) -> Tuple[List[str], int]:
        issues = []
        score = 100

        doc = fitz.open(pdf_path)
        try:
            score = self._score_font_usage(doc, issues, score)
            score = self._score_contact_info_placement(doc, issues, score)
            score = self._score_images(doc, issues, score)
            score = self._score_tables(doc, issues, score)
            score = self._score_columns(doc, issues, score)
            score = self._score_bullets(resume_text, issues, score)
            score = self._score_required_sections(cleaned_text, issues, score)
            score = self._score_length(cleaned_text, issues, score)
        finally:
            doc.close()

        return issues, max(0, score)

    def _score_font_usage(self, doc: fitz.Document, issues: List[str], score: int) -> int:
        font_sizes = {}

        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        font = span["font"]
                        size = span["size"]
                        font_sizes.setdefault(font, set()).add(size)

        if len(font_sizes) > 3:
            issues.append("Too many fonts used (recommend 1-2)")
            score -= 10

        return score

    def _score_contact_info_placement(
        self,
        doc: fitz.Document,
        issues: List[str],
        score: int,
    ) -> int:
        for page in doc:
            blocks = page.get_text("blocks")
            height = page.rect.height

            for block in blocks:
                text = block[4]
                y0 = block[1]

                if not re.search(r"\S+@\S+|\d{10}", text):
                    continue

                if y0 < 0.1 * height:
                    issues.append("Contact info in header (may be skipped by ATS)")
                    score -= 5
                elif y0 > 0.9 * height:
                    issues.append("Contact info in footer (may be skipped by ATS)")
                    score -= 5

        return score

    def _score_images(self, doc: fitz.Document, issues: List[str], score: int) -> int:
        for page in doc:
            if page.get_images():
                issues.append("Contains images (ATS may not read content)")
                return score - 15

        return score

    def _score_tables(self, doc: fitz.Document, issues: List[str], score: int) -> int:
        for page in doc:
            tables = page.find_tables()
            if tables.tables:
                issues.append("Contains tables (ATS may skip structured data)")
                return score - 10

        return score

    def _score_columns(self, doc: fitz.Document, issues: List[str], score: int) -> int:
        for page in doc:
            blocks = page.get_text("blocks")
            if not blocks:
                continue

            x_positions = [block[0] for block in blocks]
            if max(x_positions) - min(x_positions) > 300:
                issues.append("Multi-column layout detected (ATS may misread order)")
                return score - 15

        return score

    def _score_bullets(self, resume_text: str, issues: List[str], score: int) -> int:
        bullet_chars = ["\u2022", "\u00b7", "-", "*", "\u00e2\u20ac\u00a2", "\u00c2\u00b7"]

        if not any(char in resume_text for char in bullet_chars):
            issues.append("No bullet points found")
            score -= 10

        return score

    def _score_required_sections(
        self,
        cleaned_text: str,
        issues: List[str],
        score: int,
    ) -> int:
        required_sections = ["experience", "education", "skills"]
        missing_sections = [
            section for section in required_sections if section not in cleaned_text
        ]

        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
            score -= 5 * len(missing_sections)

        return score

    def _score_length(self, cleaned_text: str, issues: List[str], score: int) -> int:
        word_count = len(cleaned_text.split())

        if word_count < 200:
            issues.append("Resume too short (< 200 words)")
            score -= 20
        elif word_count > 1000:
            issues.append("Resume too long (> 1000 words)")
            score -= 10

        return score
