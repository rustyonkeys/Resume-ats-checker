"""Separate thin decorative dividers from images that warrant content review."""

import fitz

from .scoring_schema import check


def classify_images(image_info, lines, page_rect, policy):
    images = []
    for info in image_info:
        box = fitz.Rect(info["bbox"]) & page_rect
        width, height = max(0, box.width), max(0, box.height)
        short, long = sorted((width, height))
        divider = (0 < short <= policy.divider_max_thickness_pt
                   and long >= policy.divider_min_length_pt
                   and long / short >= policy.divider_min_aspect_ratio)
        overlaps_text = any(fitz.Rect(line["bbox"]).intersects(box)
                            and any(char.isalnum() for char in line["text"]) for line in lines)
        kind = "off_page" if not short else "decorative_divider" if divider else "content_image"
        images.append({"bbox": list(info["bbox"]), "classification": kind,
                       "source_pixels": info.get("width", 0) * info.get("height", 0),
                       "visible_width_pt": round(width, 2), "visible_height_pt": round(height, 2),
                       "page_area_fraction": round(width * height / max(1, page_rect.get_area()), 4),
                       "overlaps_extractable_text": overlaps_text})
    return images


def image_check(layout):
    pages = layout.get("pages", []) if layout.get("status") == "ok" else []
    unavailable = not pages or any(page["images"] is None for page in pages)
    review = [page["page"] for page in pages
              if any(image["classification"] == "content_image" for image in (page["images"] or []))]
    without_text = [page["page"] for page in pages if page["page"] in review and not page["alphanumeric_count"]]
    unresolved = any(page.get("ocr", {}).get("status") in {"unavailable", "no_text"} for page in pages)
    dividers = sum(image["classification"] == "decorative_divider"
                   for page in pages for image in (page["images"] or []))
    return check("images", 0, status="unavailable" if unavailable else "warning" if review else "pass",
                 confidence="medium",
                 message="Image analysis is unavailable on some pages." if unavailable else
                         "Non-decorative images are present on pages with no extractable text." if without_text else
                         "Non-decorative images need review for text that extraction may miss." if review else
                         "No content images detected; thin decorative dividers are ignored.",
                 suggestion="Inspect these pages and use OCR if the images contain resume text." if review else "",
                 evidence={"pages": review, "ignored_divider_count": dividers,
                           "pages_without_extractable_text": without_text,
                           "deduction_rule_id": "page_text_coverage" if without_text and not unresolved else None,
                           "note": "Page coverage is assessed under parse quality; unresolved OCR withholds deductions."})
