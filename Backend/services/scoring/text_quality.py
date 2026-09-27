"""Text extraction health and conservative encoding-noise checks."""

import unicodedata

from .scoring_schema import check, component
from .spelling_analysis import analyze_spelling
from .ocr_analysis import ocr_check
from .reading_order import reading_order_check


def score_parse_quality(features, layout):
    metrics = features["text_metrics"]
    readable = metrics["alphanumeric_count"] > 0
    checks = [check("extractable_text", 4, deduction=0 if readable else 4,
                    message="Readable characters extracted." if readable else "No readable text extracted.",
                    suggestion="Export a text-based PDF or run OCR before scoring." if not readable else "",
                    evidence={"alphanumeric_count": metrics["alphanumeric_count"]})]
    pages = layout.get("pages", [])
    unresolved_ocr = [page["page"] for page in pages
                      if page.get("ocr", {}).get("status") in {"unavailable", "no_text"}]
    if layout.get("status") != "ok" or not pages or unresolved_ocr:
        checks.append(check("page_text_coverage", 4, status="unavailable",
                            message="Per-page extraction is incomplete; unreadable content is not treated as missing content.",
                            evidence={"unresolved_ocr_pages": unresolved_ocr}))
    else:
        empty = [page["page"] for page in pages if not page["alphanumeric_count"]]
        image_pages = [page["page"] for page in pages if page["page"] in empty
                       and any(image["classification"] == "content_image" for image in (page["images"] or []))]
        checks.append(check("page_text_coverage", 4, deduction=round(4 * len(empty) / len(pages), 2),
                            message="Some pages have no readable text." if empty else "Every page contains readable text.",
                            suggestion="Inspect the listed pages; use OCR for image-based text or remove blank pages." if empty else "",
                            evidence={"pages_without_text": empty, "image_pages_without_text": image_pages,
                                      "page_count": len(pages)}))
    checks.extend([ocr_check(layout), reading_order_check(layout)])
    return component("parse_quality", checks)


def score_text_noise(text, policy, features, language="en"):
    replacement = text.count("\ufffd")
    controls = sum(unicodedata.category(char) == "Cc" and char not in "\n\r\t\f" for char in text)
    noise = replacement + controls
    ratio = noise / max(1, len(text))
    deduction = (3 if ratio >= policy.noise_fraction else 1) if noise else 0
    checks = [check("encoding_noise", 3, deduction=deduction,
                    message="Unrecognized or control characters found." if noise else "No explicit encoding errors found.",
                    suggestion="Check the PDF export and extracted text for broken characters." if noise else "",
                    evidence={"replacement_characters": replacement, "control_characters": controls,
                              "noise_ratio": round(ratio, 4)}),
              analyze_spelling(features, policy, language)]
    return component("text_noise", checks)
