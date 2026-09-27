"""Public entry point for deterministic format scoring. No LLM or network calls."""

from dataclasses import asdict

from .document_features import extract_features
from .layout_analyzer import analyze_pdf_layout, score_layout_risks, score_readability
from .scoring_schema import RULE_VERSION, WEIGHTS, ScoringPolicy, component
from .structure_scoring import score_bullets, score_contact, score_length, score_sections
from .text_quality import score_parse_quality, score_text_noise


def score_resume_format(validation_result: dict, parsed_resume: list[dict] | None = None,
                        file_path: str | None = None, *, language: str = "en",
                        policy: ScoringPolicy | None = None) -> dict:
    """Score validated extracted text and optionally inspect its source PDF.

    Pass the temporary file path before the upload handler deletes it. A complete
    score is withheld when a weighted check cannot run. Partial results include
    earned points, assessment coverage, and a provisional percentage.
    """
    if not isinstance(validation_result, dict):
        raise TypeError("validation_result must be a dictionary")
    text = validation_result.get("full_resume_text")
    if not isinstance(text, str):
        raise ValueError("validation_result.full_resume_text must be a string")
    if validation_result.get("valid") is False:
        raise ValueError("Validate the resume before format scoring")
    if parsed_resume is not None and (not isinstance(parsed_resume, list)
                                     or any(not isinstance(block, dict) for block in parsed_resume)):
        raise TypeError("parsed_resume must be a list of block dictionaries")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty language code")
    policy = policy or ScoringPolicy()
    if len(text) > policy.max_text_chars:
        raise ValueError("Resume text exceeds the scoring analysis limit")
    language = language.strip().lower().split("-")[0]
    layout = validation_result.get("pdf_analysis")
    if not isinstance(layout, dict) or layout.get("rule_version") != RULE_VERSION or layout.get("analysis_policy") != asdict(policy):
        layout = analyze_pdf_layout(file_path, policy)
    if layout.get("used_ocr") or layout.get("reading_order_repaired"):
        text = layout["extracted_text"]
    embedded_links = [link["uri"] for page in layout["pages"] for link in (page["links"] or [])]
    features = extract_features(text, parsed_resume, embedded_links)
    page_count = layout.get("page_count") if layout["status"] == "ok" else validation_result.get("page_count")
    breakdown = {
        "parse_quality": score_parse_quality(features, layout),
        "section_structure": score_sections(features, language),
        "contact_information": score_contact(features),
        "bullet_quality": score_bullets(features, policy, language),
        "length": score_length(features, page_count, policy),
        "layout_risks": score_layout_risks(layout),
        "readability": score_readability(layout, policy, language),
        "text_noise": score_text_noise(text, policy, features, language),
    }
    uncertain_pages = [page["page"] for page in layout["pages"]
                       if page["ocr"]["status"] != "not_needed" or page["reading_order"]["reordered"]
                       or (page["alphanumeric_count"] and page["reading_order"]["status"] == "unavailable")]
    if uncertain_pages:
        dependent_rules = {"skills", "education", "projects_or_experience", "contact_method",
                           "achievement_bullets", "word_count", "encoding_noise"}
        for name, part in breakdown.items():
            for item in part["checks"]:
                if item["rule_id"] in dependent_rules and item["deduction"]:
                    item.update(status="unavailable", score=None, deduction=0,
                                message="This deduction is withheld because OCR or reading-order uncertainty can affect the result.",
                                suggestion="Review extraction and section boundaries before assigning this deduction.")
                    item["evidence"]["uncertain_pages"] = uncertain_pages
            breakdown[name] = component(name, part["checks"])
    checks = [item for part in breakdown.values() for item in part["checks"]]
    assessed_score = round(sum(part["score"] for part in breakdown.values()), 2)
    assessed_max = sum(part["assessed_max_score"] for part in breakdown.values())
    maximum = sum(WEIGHTS.values())
    readable = features["text_metrics"]["alphanumeric_count"] > 0
    status = "unscorable" if not readable else "complete" if assessed_max == maximum else "partial"
    provisional = round(100 * assessed_score / assessed_max, 1) if assessed_max and readable else None
    full_score = assessed_score if status == "complete" else None
    findings = [item for item in checks if item["status"] in {"fail", "warning"}]
    return {
        "rule_version": RULE_VERSION,
        "status": status,
        "status_scope": "Weighted format checks only; advisory and unimplemented checks are listed separately.",
        "not_implemented_checks": [],
        "score": full_score,
        "max_score": maximum,
        "percentage": provisional if status == "complete" else None,
        "assessed_score": assessed_score,
        "assessed_max_score": assessed_max,
        "coverage_percentage": round(100 * assessed_max / maximum, 1),
        "provisional_percentage": provisional,
        "breakdown": breakdown,
        "issues": findings,
        "suggestions": list(dict.fromkeys(item["suggestion"] for item in findings if item["suggestion"])),
        "unavailable_checks": [item["rule_id"] for item in checks if item["status"] == "unavailable"],
        "features": features,
        "layout": layout,
        "policy": asdict(policy),
        "limitations": [
            "Heuristic format feedback, not a prediction of acceptance by any ATS.",
            "Section aliases support English; unrecognized headings need review.",
            "Contact matches are syntax candidates, not verified identities or deliverability checks.",
            "English spelling and PDF spacing are advisory heuristics; they do not deduct points.",
            "Image-only content may require OCR; image presence alone does not establish missing text.",
            "OCR recognition is unverified; original fonts cannot be measured from synthesized OCR text.",
            "Reading-order verification supports simple left-to-right single-column and two-column layouts.",
        ],
    }
