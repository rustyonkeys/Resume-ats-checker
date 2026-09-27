"""Build the compact, public API representation of format-scoring results."""


def format_validation_response(validation_result: dict) -> dict:
    """Return upload metadata without extracted text or PDF-analysis internals."""
    fields = (
        "valid",
        "extension",
        "size_bytes",
        "page_count",
        "contains_extractable_text",
        "text_extraction_method",
    )
    return {field: validation_result[field] for field in fields if field in validation_result}


def format_scoring_response(result: dict) -> dict:
    """Remove duplicated and internal scorer data from the public response."""
    pending_checks = result.get("not_implemented_checks") or []
    response = {
        "rule_version": result["rule_version"],
        "status": result["status"],
        "implementation_status": (
            "All planned checks are implemented"
            if not pending_checks
            else "Some planned checks are not implemented"
        ),
        "score": result.get("score"),
        "max_score": result["max_score"],
        "percentage": result.get("percentage"),
        "breakdown": {
            name: {
                "score": component["score"],
                "max_score": component["max_score"],
            }
            for name, component in result["breakdown"].items()
        },
        "issues": result.get("issues", []),
    }

    if pending_checks:
        response["not_implemented_checks"] = pending_checks

    unavailable_checks = result.get("unavailable_checks") or []
    if unavailable_checks:
        response["unavailable_checks"] = unavailable_checks

    if result["status"] != "complete":
        response.update({
            "assessed_score": result.get("assessed_score"),
            "assessed_max_score": result.get("assessed_max_score"),
            "coverage_percentage": result.get("coverage_percentage"),
            "provisional_percentage": result.get("provisional_percentage"),
        })

    return response
