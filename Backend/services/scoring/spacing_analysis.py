"""Compare PDF whitespace between similar sections and inferred paragraphs."""

from statistics import median

from .document_features import detect_heading, is_bullet_line, matching_text
from .scoring_schema import check


def _rows(lines):
    rows = []
    for line in sorted(lines, key=lambda item: (item["bbox"][1], item["bbox"][0])):
        if not any(char.isalnum() for char in matching_text(line["text"])):
            continue
        if rows and abs(rows[-1]["bbox"][1] - line["bbox"][1]) <= 2 and abs(rows[-1]["bbox"][3] - line["bbox"][3]) <= 3:
            row = rows[-1]
            row["text"] += " " + line["text"]
            row["bbox"] = [min(row["bbox"][0], line["bbox"][0]), min(row["bbox"][1], line["bbox"][1]),
                           max(row["bbox"][2], line["bbox"][2]), max(row["bbox"][3], line["bbox"][3])]
            row["blocks"].add(line["block"])
        else:
            rows.append({**line, "bbox": list(line["bbox"]), "blocks": {line["block"]}})
    return rows


def measure_spacing(lines, *, column_candidate=False, tables=False, rotated=False):
    if column_candidate or tables or rotated:
        return {"status": "unavailable", "reason": "Spacing needs an unrotated page without detected columns or tables.",
                "section_gaps": [], "paragraph_gaps": []}
    sections, paragraphs = [], []
    previous = None
    current_section = None
    previous_item = None
    for row in _rows(lines):
        section, inline = detect_heading(row["text"])
        heading = section is not None and not inline
        if heading:
            if previous is not None:
                sections.append({"kind": "before_heading", "section": section,
                                 "gap_pt": round(max(0, row["bbox"][1] - previous["bbox"][3]), 2),
                                 "bbox": row["bbox"]})
            current_section = row["text"]
            previous_item = None
        elif current_section and previous is not None:
            gap = round(max(0, row["bbox"][1] - previous["bbox"][3]), 2)
            previous_heading, previous_inline = detect_heading(previous["text"])
            if previous_heading and not previous_inline:
                sections.append({"kind": "after_heading", "section": previous_heading,
                                 "gap_pt": gap, "bbox": previous["bbox"]})
            bullet = is_bullet_line(row["text"])
            new_block = not row["blocks"].intersection(previous["blocks"])
            same_style = abs(row["font_size"] - previous["font_size"]) <= 1 and row["bold"] == previous["bold"]
            if bullet:
                if previous_item == "bullet" and same_style:
                    paragraphs.append({"kind": "bullet", "section": current_section,
                                       "gap_pt": gap, "bbox": row["bbox"]})
                previous_item = "bullet"
            elif new_block and same_style and previous_item == "paragraph":
                paragraphs.append({"kind": "paragraph", "section": current_section,
                                   "gap_pt": gap, "bbox": row["bbox"]})
            elif new_block or previous_item is None:
                previous_item = "paragraph"
        previous = row
    return {"status": "ok", "reason": "", "section_gaps": sections, "paragraph_gaps": paragraphs}


def spacing_checks(layout, policy, language="en"):
    output = []
    for rule_id, key in (("section_spacing", "section_gaps"), ("paragraph_spacing", "paragraph_gaps")):
        pages = layout.get("pages", []) if layout.get("status") == "ok" else []
        if language != "en" or not pages:
            output.append(check(rule_id, 0, status="unavailable",
                                message="Spacing analysis requires PDF geometry and supported English headings."))
            continue
        skipped = [page["page"] for page in pages if page["spacing"]["status"] != "ok"]
        groups = {}
        for page in pages:
            for sample in page["spacing"][key]:
                # Never compare paragraph gaps across different sections or pages.
                group = (page["page"], sample["kind"], sample["section"] if key == "paragraph_gaps" else "")
                groups.setdefault(group, []).append({**sample, "page": page["page"]})
        comparisons, outliers = [], []
        for group, samples in groups.items():
            if len(samples) < policy.spacing_min_samples:
                continue
            typical = median(sample["gap_pt"] for sample in samples)
            tolerance = max(policy.spacing_tolerance_pt, typical * policy.spacing_relative_tolerance)
            unusual = [sample for sample in samples if abs(sample["gap_pt"] - typical) > tolerance]
            comparisons.append({"page": group[0], "kind": group[1], "section": group[2],
                                "sample_count": len(samples), "median_gap_pt": round(typical, 2),
                                "tolerance_pt": round(tolerance, 2)})
            outliers.extend(unusual)
        status = "warning" if outliers else "unavailable" if skipped else "pass" if comparisons else "not_applicable"
        message = ("Uneven whitespace detected between comparable text groups." if outliers else
                   "Some pages could not be assessed for spacing." if skipped else
                   "Comparable spacing is within tolerance." if comparisons else
                   "Too few comparable gaps to judge spacing consistency.")
        output.append(check(rule_id, 0, status=status, confidence="medium" if key == "section_gaps" else "low",
                            message=message, suggestion="Review the indicated gaps; intentional spacing can be valid." if outliers else "",
                            evidence={"comparisons": comparisons, "outliers": outliers, "skipped_pages": skipped,
                                      "minimum_samples": policy.spacing_min_samples}))
    return output
