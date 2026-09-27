import unittest

from Backend.services.scoring.response_formatter import (
    format_scoring_response,
    format_validation_response,
)


class ResponseFormatterTests(unittest.TestCase):
    def test_validation_response_excludes_text_and_pdf_analysis(self):
        result = format_validation_response({
            "valid": True,
            "page_count": 1,
            "full_resume_text": "private extracted text",
            "pdf_analysis": {"pages": []},
        })

        self.assertEqual(result, {"valid": True, "page_count": 1})

    def test_complete_score_excludes_internal_and_duplicate_fields(self):
        result = format_scoring_response({
            "rule_version": "format-v1.3",
            "status": "complete",
            "not_implemented_checks": [],
            "score": 38,
            "max_score": 40,
            "percentage": 95,
            "assessed_score": 38,
            "assessed_max_score": 40,
            "coverage_percentage": 100,
            "provisional_percentage": 95,
            "breakdown": {
                "parse_quality": {
                    "score": 8,
                    "max_score": 8,
                    "assessed_max_score": 8,
                    "checks": [{"rule_id": "parse"}],
                }
            },
            "issues": [],
            "suggestions": [],
            "unavailable_checks": [],
            "features": {"lines": []},
            "layout": {"extracted_text": "duplicate"},
            "policy": {},
            "limitations": [],
        })

        self.assertEqual(result["implementation_status"], "All planned checks are implemented")
        self.assertEqual(result["breakdown"]["parse_quality"], {"score": 8, "max_score": 8})
        for field in ("features", "layout", "policy", "limitations", "suggestions",
                      "not_implemented_checks", "assessed_score", "provisional_percentage"):
            self.assertNotIn(field, result)

    def test_partial_score_keeps_coverage_and_pending_check_details(self):
        result = format_scoring_response({
            "rule_version": "format-v1.3",
            "status": "partial",
            "not_implemented_checks": ["grammar"],
            "score": None,
            "max_score": 40,
            "percentage": None,
            "assessed_score": 30,
            "assessed_max_score": 35,
            "coverage_percentage": 87.5,
            "provisional_percentage": 85.7,
            "breakdown": {},
            "issues": [],
            "unavailable_checks": ["font_usage"],
        })

        self.assertEqual(result["not_implemented_checks"], ["grammar"])
        self.assertEqual(result["unavailable_checks"], ["font_usage"])
        self.assertEqual(result["assessed_score"], 30)


if __name__ == "__main__":
    unittest.main()
