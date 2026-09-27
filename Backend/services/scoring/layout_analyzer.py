"""Bounded PDF layout analysis using the project's existing PyMuPDF dependency."""

from collections import Counter
from dataclasses import asdict
from pathlib import Path
import re

import fitz

from .image_analysis import classify_images, image_check
from .ocr_analysis import ocr_needed, run_page_ocr
from .reading_order import verify_reading_order
from .scoring_schema import RULE_VERSION, ScoringPolicy, check, component
from .spacing_analysis import measure_spacing, spacing_checks


def font_family(font):
    font = re.sub(r"^[A-Z]{6}\+", "", font)
    font = re.sub(r"(?:semibold|bold|italic|oblique|regular|medium|light|roman)", "", font, flags=re.I)
    return re.sub(r"[\s,_-]+", "", font).casefold()


def _column_candidate(lines, width, height):
    # Require substantial text on both sides of a sustained gutter. Dates alone
    # do not establish a column, and this remains advisory rather than a penalty.
    substantive = [line for line in lines if len(line["text"].split()) >= 3
                   and line["bbox"][2] - line["bbox"][0] >= width * 0.14]
    for fraction in (0.3, 0.4, 0.5, 0.6, 0.7):
        split = width * fraction
        left = [line for line in substantive if line["bbox"][2] < split - width * 0.015]
        right = [line for line in substantive if line["bbox"][0] > split + width * 0.015]
        if min(len(left), len(right)) < 4:
            continue
        top = max(min(line["bbox"][1] for line in side) for side in (left, right))
        bottom = min(max(line["bbox"][3] for line in side) for side in (left, right))
        crossing = len(substantive) - len(left) - len(right)
        if bottom - top >= height * 0.12 and crossing <= len(substantive) * 0.25:
            return {"gutter_x": round(split, 2), "left_lines": len(left), "right_lines": len(right)}
    return None


def _text_lines(data):
    lines = []
    for block_index, block in enumerate(data["blocks"]):
        for line in block.get("lines", []):
            text = "".join(span["text"] for span in line["spans"])
            if not text.strip():
                continue
            spans = [span for span in line["spans"] if any(char.isalnum() for char in span["text"])]
            bold_chars = sum(len(span["text"]) for span in spans if span["flags"] & 16)
            lines.append({"text": text, "bbox": list(line["bbox"]), "block": block_index,
                          "font_size": max((span["size"] for span in spans), default=0),
                          "bold": bold_chars > sum(len(span["text"]) for span in spans) / 2,
                          "direction": tuple(line.get("dir", (1, 0)))})
    return lines


def analyze_pdf_layout(file_path=None, policy=None):
    policy = policy or ScoringPolicy()
    result = {"status": "unavailable", "reason": "No PDF file supplied.", "pages": [], "errors": [],
              "rule_version": RULE_VERSION, "analysis_policy": asdict(policy)}
    if file_path is None:
        return result
    if Path(file_path).suffix.lower() != ".pdf":
        result["reason"] = "Visual layout analysis currently supports PDF only."
        return result
    try:
        with fitz.open(file_path) as doc:
            if not doc.is_pdf or doc.needs_pass or not 0 < doc.page_count <= policy.max_analysis_pages:
                result["reason"] = "PDF is encrypted, empty, or exceeds the analysis page limit."
                return result
            families = Counter()
            total_chars = small_chars = 0
            ocr_pages = 0
            for page in doc:
                # Exclude image bytes from text dictionaries to bound memory use.
                data = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)
                lines = _text_lines(data)
                for block in data["blocks"]:
                    for line in block.get("lines", []):
                        for span in line["spans"]:
                            count = sum(char.isalnum() for char in span["text"])
                            if not count:
                                continue
                            families[font_family(span["font"])] += count
                            total_chars += count
                            if span["size"] < policy.small_font_pt:
                                small_chars += count
                page_text = "\n".join(line["text"] for line in lines)
                item = {
                    "page": page.number + 1,
                    "width": round(page.rect.width, 2), "height": round(page.rect.height, 2),
                    "aspect_ratio": round(page.rect.width / page.rect.height, 3),
                    "alphanumeric_count": sum(char.isalnum() for char in page_text),
                    "tables": None, "images": None, "links": None,
                    "column_candidate": _column_candidate(lines, page.rect.width, page.rect.height),
                    "margins_pt": None,
                }
                if lines:
                    item["margins_pt"] = {
                        "left": round(min(line["bbox"][0] for line in lines), 2),
                        "top": round(min(line["bbox"][1] for line in lines), 2),
                        "right": round(page.rect.width - max(line["bbox"][2] for line in lines), 2),
                        "bottom": round(page.rect.height - max(line["bbox"][3] for line in lines), 2),
                    }
                try:
                    finder = page.find_tables()
                    item["tables"] = [{"bbox": list(table.bbox), "rows": table.row_count,
                                       "columns": table.col_count} for table in finder.tables]
                except Exception as exc:
                    result["errors"].append({"page": item["page"], "check": "tables", "error": type(exc).__name__})
                try:
                    item["images"] = classify_images(page.get_image_info(), lines, page.rect, policy)
                except Exception as exc:
                    result["errors"].append({"page": item["page"], "check": "images", "error": type(exc).__name__})
                try:
                    item["links"] = [{"uri": link["uri"], "bbox": list(link["from"])}
                                     for link in page.get_links()
                                     if link.get("kind") == fitz.LINK_URI and isinstance(link.get("uri"), str)]
                except Exception as exc:
                    result["errors"].append({"page": item["page"], "check": "links", "error": type(exc).__name__})
                item["native_alphanumeric_count"] = item["alphanumeric_count"]
                item["ocr"] = {"status": "not_needed", "reason": "Native extraction did not meet OCR trigger conditions."}
                item["text_source"] = "native"
                try:
                    if ocr_needed(page, lines, item["images"], policy):
                        if ocr_pages >= policy.ocr_max_pages:
                            item["ocr"] = {"status": "unavailable", "reason": "OCR page budget exhausted."}
                        elif item["native_alphanumeric_count"] and sum(
                                image["source_pixels"] for image in (item["images"] or [])) > policy.ocr_max_pixels:
                            item["ocr"] = {"status": "unavailable", "reason": "Embedded images exceed the partial OCR pixel budget."}
                        else:
                            ocr_pages += 1
                            item["ocr"], recovered = run_page_ocr(
                                file_path, page.number, page.rect.width, page.rect.height,
                                not bool(item["native_alphanumeric_count"]), policy,
                            )
                            if recovered is not None:
                                lines = _text_lines(recovered)
                                item["alphanumeric_count"] = sum(char.isalnum() for line in lines for char in line["text"])
                                item["text_source"] = "native_and_ocr" if item["native_alphanumeric_count"] else "ocr"
                                item["column_candidate"] = _column_candidate(lines, page.rect.width, page.rect.height)
                except Exception as exc:
                    item["ocr"] = {"status": "unavailable", "reason": "OCR assessment failed."}
                    result["errors"].append({"page": item["page"], "check": "ocr", "error": type(exc).__name__})
                rotated = bool(page.rotation) or any(line["direction"] != (1, 0) for line in lines)
                item["reading_order"] = verify_reading_order(
                    lines, item["column_candidate"], tables=item["tables"] is None or bool(item["tables"]), rotated=rotated,
                )
                item["spacing"] = measure_spacing(
                    lines, column_candidate=bool(item["column_candidate"]),
                    tables=item["tables"] is None or bool(item["tables"]),
                    rotated=rotated or item["text_source"] != "native",
                )
                result["pages"].append(item)
            extracted_text = "\n".join(page["reading_order"]["ordered_text"] for page in result["pages"])
            if len(extracted_text) > policy.max_text_chars:
                raise ValueError("Extracted text exceeds the analysis limit")
            result.update(status="ok", reason="", page_count=doc.page_count,
                          font_families=dict(sorted(families.items())),
                          text_character_count=total_chars,
                          small_font_fraction=round(small_chars / max(1, total_chars), 4),
                          extracted_text=extracted_text,
                          used_ocr=any(page["text_source"] != "native" for page in result["pages"]),
                          reading_order_repaired=any(page["reading_order"]["reordered"] for page in result["pages"]))
    except Exception as exc:
        result.update(status="unavailable", reason="PDF layout could not be analyzed.", pages=[])
        result["errors"].append({"check": "document", "error": type(exc).__name__})
    return result


def score_layout_risks(layout):
    checks = []
    pages = layout.get("pages", []) if layout.get("status") == "ok" else []
    for name, key, weight in (("tables", "tables", 2), ("columns", "column_candidate", 2)):
        unavailable = not pages or (key != "column_candidate" and any(page[key] is None for page in pages))
        detected = [page["page"] for page in pages if page[key]]
        checks.append(check(name, weight,
                            status="unavailable" if unavailable else "warning" if detected else "pass",
                            confidence="medium" if name != "columns" else "low",
                            message=f"Possible {name} found; presence alone does not prove extraction failure." if detected else
                                    f"{name.capitalize()} check unavailable." if unavailable else f"No {name} detected by this heuristic.",
                            suggestion="Review extracted text and reading order on these pages." if detected else "",
                            evidence={"pages": detected}))
    checks.append(image_check(layout))
    return component("layout_risks", checks)


def score_readability(layout, policy, language="en"):
    spacing = spacing_checks(layout, policy, language)
    if layout.get("status") != "ok" or not layout.get("text_character_count") or layout.get("used_ocr"):
        return component("readability", [check("font_readability", 3, status="unavailable",
                                              message="Original font information is unavailable or incomplete after OCR."), *spacing])
    # Ignore font families used only for a tiny amount of text (e.g. isolated symbols).
    families = [font for font, count in layout["font_families"].items()
                if count / layout["text_character_count"] >= 0.02]
    small = layout["small_font_fraction"] > policy.small_font_fraction
    many = len(families) > policy.max_font_families
    return component("readability", [
        check("small_body_text", 2, deduction=2 if small else 0, confidence="medium",
              message="A substantial portion of text uses small fonts." if small else "No substantial small-font text detected.",
              suggestion="Review body text size for readability." if small else "",
              evidence={"small_font_fraction": layout["small_font_fraction"],
                        "font_threshold_pt": policy.small_font_pt, "fraction_threshold": policy.small_font_fraction}),
        check("font_families", 1, deduction=1 if many else 0, confidence="medium",
              message="Many font families are used." if many else "Font family count is within the configured limit.",
              suggestion="Use fewer body-text font families." if many else "",
              evidence={"families": families, "maximum": policy.max_font_families}),
        *spacing,
    ])
