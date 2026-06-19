from typing import Dict, List, Optional, Tuple

try:
    from services.job_description_matching_service import JobDescriptionMatchingService
    from services.pdf_text_extraction_service import PDFTextExtractionService
    from services.resume_content_scoring_service import ResumeContentScoringService
    from services.resume_feature_extraction_service import ResumeFeatureExtractionService
    from services.resume_format_scoring_service import ResumeFormatScoringService
    from services.resume_text_cleaning_service import ResumeTextCleaningService
except ImportError:
    from Backend.services.job_description_matching_service import (
        JobDescriptionMatchingService,
    )
    from Backend.services.pdf_text_extraction_service import PDFTextExtractionService
    from Backend.services.resume_content_scoring_service import (
        ResumeContentScoringService,
    )
    from Backend.services.resume_feature_extraction_service import (
        ResumeFeatureExtractionService,
    )
    from Backend.services.resume_format_scoring_service import ResumeFormatScoringService
    from Backend.services.resume_text_cleaning_service import ResumeTextCleaningService


class ResumeATSScorer:
    """Coordinate resume extraction, scoring, formatting, and keyword matching."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.resume_text = ""
        self.cleaned_text = ""
        self.features: Dict[str, bool] = {}
        self.content_score = 0
        self.format_score = 0
        self.keyword_score = 0
        self.total_score = 0
        self.missing_keywords: List[str] = []
        self.matched_keywords_by_category: Dict[str, List[str]] = {}

        self.text_extraction_service = PDFTextExtractionService()
        self.text_cleaning_service = ResumeTextCleaningService()
        self.feature_extraction_service = ResumeFeatureExtractionService()
        self.content_scoring_service = ResumeContentScoringService()
        self.format_scoring_service = ResumeFormatScoringService()
        self.job_matching_service = JobDescriptionMatchingService()

    def extract_text(self) -> str:
        self.resume_text = self.text_extraction_service.extract_text(self.pdf_path)
        return self.resume_text

    def clean_text(self, text: str) -> str:
        self.cleaned_text = self.text_cleaning_service.clean_text(text)
        return self.cleaned_text

    def extract_features(self) -> Dict[str, bool]:
        self.features = self.feature_extraction_service.extract_features(
            self.cleaned_text
        )
        return self.features

    def calculate_content_score(self) -> int:
        self.content_score = self.content_scoring_service.calculate_score(self.features)
        return self.content_score

    def check_format_issues(self) -> Tuple[List[str], int]:
        issues, self.format_score = self.format_scoring_service.check_format_issues(
            self.pdf_path,
            self.resume_text,
            self.cleaned_text,
        )
        return issues, self.format_score

    def match_job_description(
        self,
        job_description: Optional[str] = None,
    ) -> Tuple[float, List[str]]:
        (
            self.keyword_score,
            matched,
            self.missing_keywords,
            self.matched_keywords_by_category,
        ) = self.job_matching_service.match(self.cleaned_text, job_description)

        return self.keyword_score, matched

    def calculate_final_score(self) -> float:
        self.total_score = (
            self.content_score * 0.4
            + self.format_score * 0.3
            + self.keyword_score * 0.3
        )
        return round(self.total_score, 2)

    def get_missing_features(self) -> List[str]:
        return [
            feature.replace("has_", "").replace("_", " ").title()
            for feature, exists in self.features.items()
            if not exists
        ]
