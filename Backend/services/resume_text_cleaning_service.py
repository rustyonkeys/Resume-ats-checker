import re


class ResumeTextCleaningService:
    """Normalize resume text before feature and keyword analysis."""

    def clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip().lower()
