"""Geometry-based verification for simple left-to-right PDF reading order."""

from .document_features import matching_text
from .scoring_schema import check


def _rows(lines):
    rows = []
    for index, line in sorted(lines, key=lambda pair: (pair[1]["bbox"][1], pair[1]["bbox"][0])):
        middle = (line["bbox"][1] + line["bbox"][3]) / 2
        if rows and abs(rows[-1]["middle"] - middle) <= 3:
            rows[-1]["items"].append((index, line))
        else:
            rows.append({"middle": middle, "items": [(index, line)]})
    for row in rows:
        row["items"].sort(key=lambda pair: pair[1]["bbox"][0])
    return rows


def verify_reading_order(lines, column_candidate=None, *, tables=False, rotated=False):
    source = [(index, line) for index, line in enumerate(lines) if matching_text(line["text"]).strip()]
    original_text = "\n".join(line["text"] for _, line in source)
    base = {"status": "unavailable", "model": None, "reordered": False,
            "ordered_text": original_text, "backward_transitions": [], "reason": ""}
    if not source:
        return {**base, "reason": "No text lines available for reading-order verification."}
    if tables or rotated:
        return {**base, "reason": "Tables or rotated text require a more specialized reading-order model."}
    if column_candidate:
        split = column_candidate["gutter_x"]
        left = [(i, line) for i, line in source if line["bbox"][2] <= split]
        right = [(i, line) for i, line in source if line["bbox"][0] >= split]
        spanning = [(i, line) for i, line in source if line["bbox"][0] < split < line["bbox"][2]]
        span_rows = _rows(spanning)
        # Full-width headers separate vertical bands; overlapping side content
        # makes a simple column interpretation unsafe.
        for _, wide in spanning:
            if any(min(wide["bbox"][3], side["bbox"][3]) - max(wide["bbox"][1], side["bbox"][1]) > 3
                   for _, side in left + right):
                return {**base, "reason": "Full-width text overlaps column content; reading order is ambiguous."}
        rows = []
        lower_bound = float("-inf")
        for wide_row in span_rows:
            upper_bound = wide_row["middle"]
            for side in (left, right):
                rows.extend(_rows([(i, line) for i, line in side
                                   if lower_bound < (line["bbox"][1] + line["bbox"][3]) / 2 < upper_bound]))
            rows.append(wide_row)
            lower_bound = upper_bound
        for side in (left, right):
            rows.extend(_rows([(i, line) for i, line in side
                               if (line["bbox"][1] + line["bbox"][3]) / 2 > lower_bound]))
        model = "two_columns_left_then_right"
    else:
        rows = _rows(source)
        model = "single_column_top_to_bottom"
    ranks = {index: rank for rank, row in enumerate(rows) for index, _ in row["items"]}
    if len(ranks) != len(source):
        return {**base, "reason": "Some text could not be assigned a reliable spatial position."}
    transitions = [{"from_line": before + 1, "to_line": after + 1}
                   for (before, _), (after, _) in zip(source, source[1:]) if ranks[after] < ranks[before]]
    text = "\n".join(" ".join(line["text"].strip() for _, line in row["items"]) for row in rows)
    return {"status": "warning" if transitions else "pass", "model": model, "reordered": bool(transitions),
            "ordered_text": text, "backward_transitions": transitions[:20],
            "reason": "Source extraction jumps backwards in the expected geometric order." if transitions else
                      "Source order agrees with the supported geometric model."}


def reading_order_check(layout):
    pages = layout.get("pages", []) if layout.get("status") == "ok" else []
    if not pages:
        return check("reading_order", 0, status="unavailable", message="Reading-order verification requires PDF geometry.")
    results = [{"page": page["page"], **{key: value for key, value in page["reading_order"].items()
                                        if key != "ordered_text"}} for page in pages]
    uncertain = any(result["status"] == "unavailable" for result in results)
    changed = any(result["reordered"] for result in results)
    return check("reading_order", 0, status="warning" if changed else "unavailable" if uncertain else "pass",
                 confidence="medium",
                 message="Text was reordered using page geometry; review the reconstructed sequence." if changed else
                         "Some pages could not be verified for reading order." if uncertain else
                         "Text order matches the supported geometric model.",
                 suggestion="Review column and section boundaries in the extracted text." if changed or uncertain else "",
                 evidence={"pages": results, "all_pages_verified": not uncertain})
