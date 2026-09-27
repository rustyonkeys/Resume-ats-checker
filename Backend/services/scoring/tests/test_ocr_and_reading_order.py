import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from uuid import uuid4

import fitz

from Backend.services.file_validation import file_validation
from Backend.services.scoring import ScoringPolicy, score_resume_format
from Backend.services.scoring.layout_analyzer import analyze_pdf_layout
from Backend.services.scoring.ocr_analysis import run_page_ocr
from Backend.services.scoring.reading_order import verify_reading_order
from Backend.services.scoring.tests.test_format_scoring import RESUME


def has_english_ocr():
    try:
        return (Path(fitz.get_tessdata()) / "eng.traineddata").is_file()
    except (RuntimeError, OSError, ValueError, TypeError):
        return False


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parent / f"fixture_{uuid4().hex}.pdf"
        self.addCleanup(self.path.unlink, missing_ok=True)
        self.policy = ScoringPolicy()

    @staticmethod
    def line(text, x, y, width=200):
        return {"text": text, "bbox": [x, y, x + width, y + 12]}

    @staticmethod
    def rule(result, name):
        return next(rule for part in result["breakdown"].values() for rule in part["checks"] if rule["rule_id"] == name)

    def make_scan(self, mixed=False, pages=1):
        with fitz.open() as source:
            page = source.new_page()
            page.insert_text((40, 45), RESUME, fontsize=11)
            bitmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        with fitz.open() as document:
            for _ in range(pages):
                page = document.new_page()
                if mixed:
                    page.insert_text((40, 25), "Native header remains available", fontsize=11)
                    box = fitz.Rect(0, 70, 595, 842)
                else:
                    box = page.rect
                page.insert_image(box, pixmap=bitmap, keep_proportion=False)
            document.save(self.path, deflate=True)
        return self.path

    def test_single_column_reading_order_is_verified(self):
        lines = [self.line("Skills", 40, 40), self.line("Python SQL", 40, 60), self.line("Education", 40, 80)]
        result = verify_reading_order(lines)
        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["reordered"])

    def test_backwards_single_column_extraction_is_repaired(self):
        lines = [self.line("Education", 40, 80), self.line("Skills", 40, 40), self.line("Python SQL", 40, 60)]
        result = verify_reading_order(lines)
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["ordered_text"].splitlines(), ["Skills", "Python SQL", "Education"])

    def test_aligned_job_dates_do_not_create_false_backward_transitions(self):
        lines = [self.line("Company role", 40, 40), self.line("2020 - 2024", 440, 40, 100),
                 self.line("Built a service", 40, 60)]
        self.assertEqual(verify_reading_order(lines)["status"], "pass")

    def test_interleaved_columns_are_repaired_with_header_preserved(self):
        lines = [self.line("Full width header", 40, 20, 500),
                 self.line("Skills", 40, 60), self.line("Experience", 340, 60),
                 self.line("Python and SQL", 40, 80), self.line("Built a service", 340, 80)]
        result = verify_reading_order(lines, {"gutter_x": 300})
        self.assertEqual(result["ordered_text"].splitlines(),
                         ["Full width header", "Skills", "Python and SQL", "Experience", "Built a service"])
        self.assertTrue(result["reordered"])

    def test_already_ordered_columns_do_not_warn(self):
        lines = [self.line("Skills", 40, 60), self.line("Python and SQL", 40, 80),
                 self.line("Experience", 340, 60), self.line("Built a service", 340, 80)]
        self.assertEqual(verify_reading_order(lines, {"gutter_x": 300})["status"], "pass")

    def test_ambiguous_or_unsupported_layout_is_not_verified(self):
        lines = [self.line("Spanning text", 40, 60, 500), self.line("Side content", 340, 60)]
        self.assertEqual(verify_reading_order(lines, {"gutter_x": 300})["status"], "unavailable")
        self.assertEqual(verify_reading_order(lines, tables=True)["status"], "unavailable")
        self.assertEqual(verify_reading_order(lines, rotated=True)["status"], "unavailable")
        self.assertEqual(verify_reading_order([])["status"], "unavailable")

    def test_pdf_column_repair_reaches_validation_and_section_features(self):
        left = ["Skills", "Python SQL and testing", "Education", "University degree and research",
                "Academic study and practice", "Technical courses and projects", "Student community activities"]
        right = ["Experience", "- Built a useful application", "- Tested a useful application",
                 "- Documented a useful application", "- Released a useful application",
                 "- Improved a useful application", "- Maintained a useful application"]
        with fitz.open() as doc:
            page = doc.new_page()
            for index, (a, b) in enumerate(zip(left, right)):
                page.insert_text((40, 60 + index * 30), a, fontsize=10)
                page.insert_text((340, 60 + index * 30), b, fontsize=10)
            doc.save(self.path)
        validation = file_validation(self.path, {".pdf"}, 5)
        self.assertTrue(validation["pdf_analysis"]["reading_order_repaired"])
        self.assertLess(validation["full_resume_text"].index("Skills"), validation["full_resume_text"].index("Experience"))
        result = score_resume_format(validation, file_path=self.path)
        sections = result["features"]["sections"]
        self.assertEqual([section["type"] for section in sections], ["skills", "education", "experience"])
        self.assertEqual(self.rule(result, "reading_order")["status"], "warning")

    def test_native_text_does_not_invoke_ocr(self):
        with fitz.open() as doc:
            doc.new_page().insert_text((40, 40), RESUME, fontsize=11)
            doc.save(self.path)
        with patch("Backend.services.scoring.layout_analyzer.run_page_ocr") as worker:
            validation = file_validation(self.path, {".pdf"}, 5)
        worker.assert_not_called()
        self.assertEqual(validation["text_extraction_method"], "native")

    def test_blank_page_does_not_invoke_ocr(self):
        with fitz.open() as doc:
            doc.new_page()
            doc.save(self.path)
        with patch("Backend.services.scoring.layout_analyzer.run_page_ocr") as worker:
            layout = analyze_pdf_layout(self.path)
        worker.assert_not_called()
        self.assertEqual(layout["pages"][0]["ocr"]["status"], "not_needed")

    @unittest.skipUnless(has_english_ocr(), "English Tesseract language data is not installed")
    def test_real_scanned_resume_survives_validation_and_scoring(self):
        self.make_scan()
        validation = file_validation(self.path, {".pdf"}, 5)
        self.assertEqual(validation["text_extraction_method"], "ocr_assisted")
        self.assertIn("EDUCATION", validation["full_resume_text"])
        self.assertIn("PROJECTS", validation["full_resume_text"])
        with patch("Backend.services.scoring.resume_format_scoring.analyze_pdf_layout") as repeated:
            result = score_resume_format(validation, file_path=self.path)
        repeated.assert_not_called()
        self.assertEqual(result["layout"]["pages"][0]["ocr"]["status"], "recovered")
        self.assertEqual(result["breakdown"]["parse_quality"]["score"], 8)
        self.assertEqual(self.rule(result, "font_readability")["status"], "unavailable")
        self.assertEqual(result["status"], "partial")
        json.dumps(result, allow_nan=False)

    @unittest.skipUnless(has_english_ocr(), "English Tesseract language data is not installed")
    def test_partial_ocr_keeps_native_header_and_recovers_image_text(self):
        self.make_scan(mixed=True)
        validation = file_validation(self.path, {".pdf"}, 5)
        self.assertIn("Native header remains available", validation["full_resume_text"])
        self.assertIn("EDUCATION", validation["full_resume_text"])
        self.assertEqual(validation["pdf_analysis"]["pages"][0]["ocr"]["mode"], "partial")

    def test_unavailable_ocr_does_not_create_missing_section_penalties(self):
        self.make_scan(mixed=True)
        with patch("Backend.services.scoring.layout_analyzer.run_page_ocr",
                   return_value=({"status": "unavailable", "reason": "Engine unavailable"}, None)):
            result = score_resume_format({"full_resume_text": "Native header remains available"}, file_path=self.path)
        for name in ("skills", "education", "contact_method", "word_count", "page_text_coverage"):
            self.assertEqual(self.rule(result, name)["status"], "unavailable")
            self.assertEqual(self.rule(result, name)["deduction"], 0)
        self.assertIsNone(result["score"])

    def test_failed_scan_validation_has_a_specific_reason(self):
        self.make_scan()
        with patch("Backend.services.scoring.layout_analyzer.run_page_ocr",
                   return_value=({"status": "unavailable", "reason": "Required language data missing"}, None)):
            with self.assertRaisesRegex(ValueError, "language data missing"):
                file_validation(self.path, {".pdf"}, 5)

    def test_page_budget_is_enforced(self):
        self.make_scan(pages=2)
        with patch("Backend.services.scoring.layout_analyzer.run_page_ocr",
                   return_value=({"status": "no_text", "reason": "No text recognized"}, None)) as worker:
            layout = analyze_pdf_layout(self.path, ScoringPolicy(ocr_max_pages=1))
        self.assertEqual(worker.call_count, 1)
        self.assertIn("budget", layout["pages"][1]["ocr"]["reason"])

    def test_ocr_can_be_disabled(self):
        status, data = run_page_ocr(self.path, 0, 595, 842, True, ScoringPolicy(ocr_enabled=False))
        self.assertEqual(status["status"], "unavailable")
        self.assertIsNone(data)

    def test_missing_language_data_is_reported(self):
        with patch("Backend.services.scoring.ocr_analysis.fitz.get_tessdata", return_value=str(self.path)):
            status, _ = run_page_ocr(self.path, 0, 595, 842, True, self.policy)
        self.assertIn("missing", status["reason"])

    def test_timeout_and_invalid_engine_output_are_reported(self):
        with patch("Backend.services.scoring.ocr_analysis.fitz.get_tessdata", return_value="."):
            with patch("Backend.services.scoring.ocr_analysis.Path.is_file", return_value=True):
                with patch("Backend.services.scoring.ocr_analysis.subprocess.run",
                           side_effect=subprocess.TimeoutExpired("worker", 1)):
                    status, _ = run_page_ocr(self.path, 0, 595, 842, True, self.policy)
                self.assertIn("time limit", status["reason"])
                with patch("Backend.services.scoring.ocr_analysis.subprocess.run",
                           return_value=subprocess.CompletedProcess([], 0, "not JSON", "")):
                    status, _ = run_page_ocr(self.path, 0, 595, 842, True, self.policy)
                self.assertEqual(status["status"], "unavailable")

    def test_pixel_budget_prevents_oversized_render(self):
        with patch("Backend.services.scoring.ocr_analysis.fitz.get_tessdata", return_value="."):
            with patch("Backend.services.scoring.ocr_analysis.Path.is_file", return_value=True):
                with patch("Backend.services.scoring.ocr_analysis.subprocess.run") as worker:
                    status, _ = run_page_ocr(self.path, 0, 100000, 100000, True, self.policy)
        worker.assert_not_called()
        self.assertIn("pixel budget", status["reason"])

    def test_partial_ocr_image_pixel_budget_is_enforced_before_worker(self):
        self.make_scan(mixed=True)
        with patch("Backend.services.scoring.layout_analyzer.run_page_ocr") as worker:
            layout = analyze_pdf_layout(self.path, ScoringPolicy(ocr_max_pixels=1000))
        worker.assert_not_called()
        self.assertIn("pixel budget", layout["pages"][0]["ocr"]["reason"])

    def test_invalid_ocr_settings_are_rejected(self):
        for kwargs in ({"ocr_enabled": "yes"}, {"ocr_language": "../eng"}, {"ocr_dpi": 0},
                       {"ocr_max_pages": 0}, {"ocr_image_min_area": float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ScoringPolicy(**kwargs)


if __name__ == "__main__":
    unittest.main()
