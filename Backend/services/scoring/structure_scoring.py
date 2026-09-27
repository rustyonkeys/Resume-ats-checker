"""Explainable section, contact, bullet, and length rules."""

from .document_features import WORD, is_bullet_line
from .scoring_schema import check, component


def score_sections(features, language="en"):
    checks = []
    groups = [("skills", {"skills"}, 2), ("education", {"education"}, 2),
              ("projects_or_experience", {"projects", "experience"}, 3)]
    for name, accepted, weight in groups:
        matches = [section for section in features["sections"] if section["type"] in accepted]
        populated = [section for section in matches
                     if any(not line.get("is_subheading") and any(char.isalnum() for char in line["text"])
                            for line in section["lines"])]
        checks.append(check(
            name, weight, deduction=0 if populated or language != "en" else weight,
            status="unavailable" if language != "en" else None,
            confidence="medium",
            message=("Section aliases currently support English only." if language != "en" else
                     "Recognized a section with content." if populated else
                     "No populated section recognized by the heading rules."),
            suggestion="Check the heading and section content." if not populated and language == "en" else "",
            evidence={"accepted_types": sorted(accepted), "heading_lines": [s["line"] for s in matches]}))
    return component("section_structure", checks)


def score_contact(features):
    contact = features["contact_info"]
    reachable = bool(contact["emails"] or contact["phones"])
    checks = [check("contact_method", 5, deduction=0 if reachable else 5, confidence="medium",
                    message="An email or phone candidate was found." if reachable else "No email or phone recognized.",
                    suggestion="Include a readable email address or phone number." if not reachable else "",
                    evidence={"email_count": len(contact["emails"]), "phone_count": len(contact["phones"]),
                              "link_count": len(contact["links"])})]
    return component("contact_information", checks)


def score_bullets(features, policy, language="en"):
    # Count logical list items, including wrapped lines, within achievement sections.
    sections = [s for s in features["sections"] if s["type"] in {"experience", "projects"} and s["lines"]]
    if not sections or language != "en":
        return component("bullet_quality", [check("achievement_bullets", 5, status="unavailable",
                         message="No supported achievement section available for bullet analysis.")])
    items = []
    missing = []
    for section in sections:
        current = None
        found = False
        for line in section["lines"]:
            if is_bullet_line(line["text"]):
                current = {"line": line["line"], "word_count": len(WORD.findall(line["text"]))}
                items.append(current)
                found = True
            elif current is not None:
                current["word_count"] += len(WORD.findall(line["text"]))
        if not found:
            missing.append(section["line"])
    long_items = [item for item in items if item["word_count"] > policy.long_bullet_words]
    checks = [check("achievement_bullets", 3, deduction=1 if missing else 0, confidence="medium",
                    message="Some achievement sections have no recognized bullets." if missing else "Achievement bullets found.",
                    suggestion="Use consistent list markers for achievement statements." if missing else "",
                    evidence={"section_lines_without_bullets": missing, "bullet_count": len(items)}),
              check("long_bullets", 2, status="warning" if long_items else "pass", confidence="low",
                    message="Some bullet groups may be long; wrapped lines can include job headings." if long_items else "No long bullet groups detected.",
                    suggestion="Review the listed bullet groups for concise wording." if long_items else "",
                    evidence={"items": long_items, "threshold_words": policy.long_bullet_words})]
    return component("bullet_quality", checks)


def score_length(features, page_count, policy):
    words = features["text_metrics"]["word_count"]
    outside_range = words < policy.min_words or words > policy.max_words
    checks = [check("word_count", 2, deduction=1 if outside_range else 0, confidence="medium",
                    message="Word count falls outside the configured resume range." if outside_range else "Word count is within the configured range.",
                    suggestion="Review content length for your career stage." if outside_range else "",
                    evidence={"word_count": words, "min_words": policy.min_words, "max_words": policy.max_words})]
    known = type(page_count) is int and page_count > 0
    long = known and page_count > policy.max_pages
    checks.append(check("page_count", 3, deduction=min(3, page_count - policy.max_pages) if long else 0,
                        status=None if known else "unavailable", confidence="medium",
                        message="Page count exceeds the configured limit." if long else
                                "Page count is within the configured limit." if known else "Page count is unavailable.",
                        suggestion="Review whether the extra pages are needed for this application." if long else "",
                        evidence={"page_count": page_count if known else None, "max_pages": policy.max_pages}))
    return component("length", checks)
