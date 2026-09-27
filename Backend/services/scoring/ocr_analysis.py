"""Bounded local OCR, with explicit unavailable and recognition-failure states."""

import json
import math
from pathlib import Path
import subprocess
import sys

import fitz

from .scoring_schema import check


def ocr_needed(page, lines, images, policy):
    native_chars = sum(char.isalnum() for line in lines for char in line["text"])
    for image in images or []:
        if image["classification"] != "content_image":
            continue
        box = fitz.Rect(image["bbox"])
        overlapping_chars = sum(char.isalnum() for line in lines if fitz.Rect(line["bbox"]).intersects(box)
                                for char in line["text"])
        if not native_chars or (image["page_area_fraction"] >= policy.ocr_image_min_area and overlapping_chars < 40):
            return True
    # Text converted to vector outlines also needs OCR. A genuinely blank page does not.
    return not native_chars and bool(page.get_drawings())


def run_page_ocr(path, page_index, width, height, full, policy):
    if not policy.ocr_enabled:
        return {"status": "unavailable", "reason": "OCR is disabled by policy."}, None
    try:
        tessdata = fitz.get_tessdata()
        if any(not (Path(tessdata) / f"{lang}.traineddata").is_file() for lang in policy.ocr_language.split("+")):
            return {"status": "unavailable", "reason": "Required Tesseract language data is missing."}, None
    except (RuntimeError, OSError, ValueError, TypeError):
        return {"status": "unavailable", "reason": "Tesseract language data could not be located."}, None
    dpi = min(policy.ocr_dpi, math.floor(72 * math.sqrt(policy.ocr_max_pixels / max(1, width * height))))
    if dpi < 72:
        return {"status": "unavailable", "reason": "Page dimensions exceed the OCR pixel budget."}, None
    request = {"path": str(Path(path).resolve()), "page": page_index, "full": full,
               "dpi": dpi, "language": policy.ocr_language, "tessdata": tessdata}
    try:
        process = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("ocr_worker.py"))],
            input=json.dumps(request), capture_output=True, text=True, encoding="utf-8",
            timeout=policy.ocr_timeout_seconds,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if process.returncode:
            return {"status": "unavailable", "reason": "The local OCR engine failed."}, None
        data = json.loads(process.stdout)
        if not isinstance(data, dict) or not isinstance(data.get("blocks"), list):
            raise ValueError("Invalid OCR output")
        recognized = sum(char.isalnum() for block in data["blocks"] for line in block.get("lines", [])
                         for span in line["spans"] if span["font"] == "GlyphLessFont" for char in span["text"])
        return {"status": "recovered" if recognized else "no_text",
                "reason": "OCR text needs review for recognition errors." if recognized else
                          "OCR found no readable text; this does not establish missing resume content.",
                "recognized_characters": recognized, "language": policy.ocr_language,
                "dpi": dpi, "mode": "full" if full else "partial"}, data if recognized else None
    except subprocess.TimeoutExpired:
        return {"status": "unavailable", "reason": "OCR exceeded the per-page time limit."}, None
    except (OSError, ValueError, KeyError, TypeError):
        return {"status": "unavailable", "reason": "OCR output could not be read."}, None


def ocr_check(layout):
    pages = layout.get("pages", []) if layout.get("status") == "ok" else []
    if not pages:
        return check("ocr", 0, status="unavailable", message="OCR assessment requires a readable PDF.")
    attempted = [{"page": page["page"], **page["ocr"]} for page in pages if page["ocr"]["status"] != "not_needed"]
    unavailable = any(item["status"] == "unavailable" for item in attempted)
    return check("ocr", 0, status="unavailable" if unavailable else "warning" if attempted else "not_applicable",
                 message="Some OCR pages could not be processed." if unavailable else
                         "OCR was attempted; review recognition before relying on the text." if attempted else
                         "No pages met the OCR trigger conditions.",
                 suggestion="Review the recovered text or upload a text-based PDF." if attempted else "",
                 confidence="medium", evidence={"pages": attempted})
