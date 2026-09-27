"""Versioned rules and JSON-serializable scoring results."""

from dataclasses import dataclass


RULE_VERSION = "format-v1.3"
WEIGHTS = {
    "parse_quality": 8,
    "section_structure": 7,
    "contact_information": 5,
    "bullet_quality": 5,
    "length": 5,
    "layout_risks": 4,
    "readability": 3,
    "text_noise": 3,
}


@dataclass(frozen=True)
class ScoringPolicy:
    """Initial resume heuristics, to be calibrated on labelled resumes."""

    min_words: int = 150
    max_words: int = 1200
    max_pages: int = 2
    long_bullet_words: int = 45
    small_font_pt: float = 9.0
    small_font_fraction: float = 0.2
    max_font_families: int = 3
    noise_fraction: float = 0.01
    max_analysis_pages: int = 30
    max_text_chars: int = 200_000
    divider_max_thickness_pt: float = 2.0
    divider_min_length_pt: float = 20.0
    divider_min_aspect_ratio: float = 20.0
    spacing_tolerance_pt: float = 4.0
    spacing_relative_tolerance: float = 0.5
    spacing_min_samples: int = 3
    spelling_max_candidates: int = 50
    spelling_allowed_words: tuple[str, ...] = ()
    ocr_enabled: bool = True
    ocr_language: str = "eng"
    ocr_dpi: int = 180
    ocr_max_pages: int = 3
    ocr_timeout_seconds: int = 20
    ocr_max_pixels: int = 12_000_000
    ocr_image_min_area: float = 0.08

    def __post_init__(self):
        for name in ("min_words", "max_words", "max_pages", "long_bullet_words",
                     "max_font_families", "max_analysis_pages", "max_text_chars",
                     "spacing_min_samples", "spelling_max_candidates", "ocr_dpi", "ocr_max_pages",
                     "ocr_timeout_seconds", "ocr_max_pixels"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.min_words > self.max_words:
            raise ValueError("min_words must not exceed max_words")
        if not 0 < self.small_font_pt < 100:
            raise ValueError("small_font_pt must be between 0 and 100")
        for name in ("small_font_fraction", "noise_fraction"):
            if not 0 < getattr(self, name) <= 1:
                raise ValueError(f"{name} must be in (0, 1]")
        for name in ("divider_max_thickness_pt", "divider_min_length_pt", "divider_min_aspect_ratio",
                     "spacing_tolerance_pt", "spacing_relative_tolerance"):
            if not 0 < getattr(self, name) < float("inf"):
                raise ValueError(f"{name} must be a finite positive number")
        if not isinstance(self.spelling_allowed_words, tuple) or any(
                not isinstance(word, str) or not word.strip() for word in self.spelling_allowed_words):
            raise ValueError("spelling_allowed_words must be a tuple of non-empty words")
        if type(self.ocr_enabled) is not bool:
            raise ValueError("ocr_enabled must be a boolean")
        if not isinstance(self.ocr_language, str) or not self.ocr_language or any(
                not part.isalpha() or not part.isascii() for part in self.ocr_language.split("+")):
            raise ValueError("ocr_language must contain Tesseract language codes such as eng or eng+hin")
        if not 0 < self.ocr_image_min_area <= 1:
            raise ValueError("ocr_image_min_area must be in (0, 1]")


def check(rule_id, max_score, *, deduction=0, status=None, message="",
          suggestion="", evidence=None, confidence="high"):
    if not 0 <= deduction <= max_score:
        raise ValueError(f"Invalid deduction for {rule_id}")
    status = status or ("fail" if deduction else "pass")
    if status not in {"pass", "fail", "warning", "unavailable", "not_applicable"}:
        raise ValueError(f"Invalid status for {rule_id}")
    return {
        "rule_id": rule_id,
        "status": status,
        "score": None if status in {"unavailable", "not_applicable"} else max_score - deduction,
        "max_score": max_score,
        "deduction": deduction,
        "confidence": confidence,
        "message": message,
        "suggestion": suggestion,
        "evidence": evidence or {},
    }


def component(name, checks):
    if sum(item["max_score"] for item in checks) != WEIGHTS[name]:
        raise ValueError(f"Check weights do not match {name}")
    assessed = [item for item in checks if item["score"] is not None]
    return {
        "score": round(sum(item["score"] for item in assessed), 2),
        "max_score": WEIGHTS[name],
        "assessed_max_score": sum(item["max_score"] for item in assessed),
        "checks": checks,
    }
