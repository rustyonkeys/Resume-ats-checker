import re
from typing import Dict


class ResumeFeatureExtractionService:
    """Detect contact details, core sections, and quality signals."""

    def extract_features(self, cleaned_text: str) -> Dict[str, bool]:
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        phone_pattern = (
            r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|"
            r"\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|"
            r"\+\d{1,2}\s?\d{10})"
        )

        emails = re.findall(email_pattern, cleaned_text)
        phones = re.findall(phone_pattern, cleaned_text)

        return {
            "email": len(emails) > 0,
            "phone": len(phones) > 0,
            "has_experience": "experience" in cleaned_text,
            "has_education": "education" in cleaned_text,
            "has_skills": "skills" in cleaned_text,
            "has_projects": "projects" in cleaned_text,
            "has_certifications": "certifications" in cleaned_text,
            "has_summary": any(
                word in cleaned_text for word in ["summary", "objective", "profile"]
            ),
            "has_achievements": any(
                word in cleaned_text
                for word in ["achieved", "improved", "increased", "reduced"]
            ),
            "has_metrics": bool(re.search(r"\d+%|\$\d+|[\d,]+\+", cleaned_text)),
        }
