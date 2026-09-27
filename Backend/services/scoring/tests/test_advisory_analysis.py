import json
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

import fitz

from Backend.services.scoring import ScoringPolicy, score_resume_format
from Backend.services.scoring.document_features import extract_features
from Backend.services.scoring.image_analysis import classify_images
from Backend.services.scoring.spacing_analysis import measure_spacing, spacing_checks
from Backend.services.scoring.spelling_analysis import analyze_spelling
from Backend.services.scoring.tests.test_format_scoring import RESUME


class AdvisoryAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parent / f"fixture_{uuid4().hex}.pdf"
        self.addCleanup(self.path.unlink, missing_ok=True)
        self.policy = ScoringPolicy()

    @staticmethod
    def rule(result, name):
        return next(rule for part in result["breakdown"].values() for rule in part["checks"] if rule["rule_id"] == name)

    @staticmethod
    def line(text, top, block, left=40, bold=False):
        return {"text": text, "bbox": [left, top, left + 200, top + 10],
                "block": block, "font_size": 10, "bold": bold}

    def spacing_result(self, lines, **kwargs):
        measurements = measure_spacing(lines, **kwargs)
        checks = spacing_checks({"status": "ok", "pages": [{"page": 1, "spacing": measurements}]}, self.policy)
        return {check["rule_id"]: check for check in checks}

    def save_image_pdf(self, box, image_only_second_page=False):
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_text((45, 40), RESUME, fontsize=11)
            if image_only_second_page:
                page = doc.new_page()
            with fitz.open() as source:
                source.new_page().insert_text((30, 30), "This text is only available inside the image")
                bitmap = source[0].get_pixmap()
            page.insert_image(fitz.Rect(box), pixmap=bitmap, keep_proportion=False)
            doc.save(self.path)
        return score_resume_format({"valid": True, "full_resume_text": RESUME}, file_path=self.path)

    def test_horizontal_and_vertical_dividers_are_classified(self):
        images = classify_images([{"bbox": [40, 40, 540, 41]}, {"bbox": [40, 60, 41, 560]}],
                                 [], fitz.Rect(0, 0, 600, 800), self.policy)
        self.assertEqual([image["classification"] for image in images], ["decorative_divider"] * 2)

    def test_images_icons_and_banners_are_not_mislabeled_as_dividers(self):
        images = classify_images([{"bbox": [40, 40, 140, 140]}, {"bbox": [40, 200, 540, 220]},
                                  {"bbox": [20, 20, 21, 21]}], [], fitz.Rect(0, 0, 600, 800), self.policy)
        self.assertTrue(all(image["classification"] == "content_image" for image in images))

    def test_off_page_image_does_not_warn(self):
        images = classify_images([{"bbox": [700, 900, 800, 1000]}], [], fitz.Rect(0, 0, 600, 800), self.policy)
        self.assertEqual(images[0]["classification"], "off_page")

    def test_pdf_divider_warning_is_suppressed(self):
        result = self.save_image_pdf((40, 600, 540, 601))
        self.assertEqual(self.rule(result, "images")["status"], "pass")
        self.assertEqual(self.rule(result, "images")["evidence"]["ignored_divider_count"], 1)
        self.assertEqual(result["score"], 40)

    def test_regular_image_warns_without_presence_penalty(self):
        result = self.save_image_pdf((40, 600, 140, 700))
        image = self.rule(result, "images")
        self.assertEqual(image["status"], "warning")
        self.assertEqual(image["deduction"], 0)
        self.assertIsNone(image["evidence"]["deduction_rule_id"])
        self.assertEqual(result["score"], 40)

    def test_unresolved_image_only_page_is_not_a_missing_content_penalty(self):
        with patch("Backend.services.scoring.layout_analyzer.run_page_ocr",
                   return_value=({"status": "unavailable", "reason": "OCR engine unavailable"}, None)):
            result = self.save_image_pdf((0, 0, 595, 842), image_only_second_page=True)
        image = self.rule(result, "images")
        coverage = self.rule(result, "page_text_coverage")
        self.assertEqual(image["evidence"]["pages_without_extractable_text"], [2])
        self.assertIsNone(image["evidence"]["deduction_rule_id"])
        self.assertEqual(coverage["evidence"]["unresolved_ocr_pages"], [2])
        self.assertEqual(coverage["status"], "unavailable")
        self.assertEqual(coverage["deduction"], 0)
        self.assertIsNone(result["score"])

    def test_text_layer_overlap_is_reported_without_ocr_claim(self):
        image = classify_images([{"bbox": [0, 0, 600, 800]}], [self.line("Readable text", 100, 0)],
                                fitz.Rect(0, 0, 600, 800), self.policy)[0]
        self.assertTrue(image["overlaps_extractable_text"])
        self.assertEqual(image["classification"], "content_image")

    def test_image_detector_failure_is_explicit(self):
        self.save_image_pdf((40, 600, 540, 601))
        with patch.object(fitz.Page, "get_image_info", side_effect=RuntimeError("failed")):
            result = score_resume_format({"full_resume_text": RESUME}, file_path=self.path)
        self.assertEqual(self.rule(result, "images")["status"], "unavailable")
        self.assertIn("images", result["unavailable_checks"])

    def test_spelling_finds_typo_with_suggestions_and_source_line(self):
        text = "Experience\n- Developd a reliable application with clear documentation and testing."
        result = analyze_spelling(extract_features(text), self.policy)
        self.assertEqual(result["status"], "warning")
        candidate = next(word for word in result["evidence"]["candidates"] if word["word"] == "developd")
        self.assertIn("developed", candidate["suggestions"])
        self.assertEqual(candidate["lines"], [2])
        self.assertEqual(result["deduction"], 0)

    def test_names_acronyms_urls_and_domain_terms_are_filtered(self):
        text = ("Zarvik Person\nSkills\nVeloraDB, Kubernetes, PyTorch\nExperience\n"
                "- Built veloradb tools with kubernetes and PyTorch for Zarvik using SQL.\n"
                "- Documented the service at https://example.com/unknownword with clear examples.")
        result = analyze_spelling(extract_features(text), self.policy)
        self.assertEqual(result["status"], "pass")

    def test_allowlist_does_not_leak_between_resumes(self):
        features = extract_features("Projects\n- Developd a reliable application with clear documentation and testing.")
        allowed = analyze_spelling(features, ScoringPolicy(spelling_allowed_words=("developd",)))
        default = analyze_spelling(features, self.policy)
        self.assertEqual(allowed["status"], "pass")
        self.assertEqual(default["status"], "warning")

    def test_preprocessing_vocabulary_is_not_a_typo(self):
        text = ("Projects\n- Built tools to preprocess documents before using preprocessing routines.\n"
                "- The system preprocesses the files and stores preprocessed results.")
        self.assertEqual(analyze_spelling(extract_features(text), self.policy)["status"], "pass")

    def test_unsupported_language_and_missing_dictionary_are_unavailable(self):
        features = extract_features(RESUME)
        self.assertEqual(analyze_spelling(features, self.policy, "fr")["status"], "unavailable")
        with patch("Backend.services.scoring.spelling_analysis._dictionary", side_effect=ImportError):
            result = analyze_spelling(features, self.policy)
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("requirements", result["suggestion"])

    def test_short_or_absent_prose_is_not_applicable(self):
        result = analyze_spelling(extract_features("Skills\nPython\nEducation\nBSc"), self.policy)
        self.assertEqual(result["status"], "not_applicable")

    def test_spelling_candidate_limit_is_disclosed(self):
        text = "Experience\n- Developd a relaiable application with documantation for all users."
        result = analyze_spelling(extract_features(text), ScoringPolicy(spelling_max_candidates=1))
        self.assertTrue(result["evidence"]["truncated"])
        self.assertEqual(len(result["evidence"]["candidates"]), 1)

    def test_consistent_section_gaps_pass(self):
        lines = []
        for index, heading in enumerate(("Skills", "Education", "Experience", "Projects")):
            lines += [self.line(heading, 20 + 80 * index, 2 * index, bold=True),
                      self.line("Section content", 40 + 80 * index, 2 * index + 1)]
        self.assertEqual(self.spacing_result(lines)["section_spacing"]["status"], "pass")

    def test_section_gap_outlier_has_geometry_evidence(self):
        lines = []
        for index, (heading, top) in enumerate(zip(("Skills", "Education", "Experience", "Projects"), (20, 100, 180, 300))):
            lines += [self.line(heading, top, 2 * index, bold=True),
                      self.line("Section content", top + 20, 2 * index + 1)]
        check = self.spacing_result(lines)["section_spacing"]
        self.assertEqual(check["status"], "warning")
        self.assertEqual(check["evidence"]["outliers"][0]["gap_pt"], 90)
        self.assertEqual(check["deduction"], 0)

    def test_paragraph_gap_outlier_is_compared_inside_one_section(self):
        lines = [self.line("Projects", 10, 0, bold=True)]
        lines += [self.line("Built a useful application for student volunteers.", y, i + 1)
                  for i, y in enumerate((30, 50, 70, 120))]
        check = self.spacing_result(lines)["paragraph_spacing"]
        self.assertEqual(check["status"], "warning")
        self.assertEqual(check["evidence"]["outliers"][0]["gap_pt"], 40)

    def test_wrapped_bullets_do_not_count_as_new_paragraphs(self):
        lines = [self.line("Projects", 10, 0, bold=True),
                 self.line("- Built a useful application", 30, 1),
                 self.line("with a wrapped continuation", 42, 1),
                 self.line("- Tested it carefully", 62, 2),
                 self.line("with another continuation", 74, 2),
                 self.line("- Added documentation", 94, 3),
                 self.line("- Released a version", 114, 4)]
        check = self.spacing_result(lines)["paragraph_spacing"]
        self.assertEqual(check["status"], "pass")
        self.assertEqual(check["evidence"]["comparisons"][0]["sample_count"], 3)

    def test_distinct_sections_are_not_compared_for_paragraph_spacing(self):
        lines = [self.line("Projects", 10, 0)]
        lines += [self.line("- Built a useful application", y, i + 1) for i, y in enumerate((30, 50, 70, 90))]
        lines += [self.line("Experience", 150, 5)]
        lines += [self.line("- Built another application", y, i + 6) for i, y in enumerate((170, 220, 270, 320))]
        check = self.spacing_result(lines)["paragraph_spacing"]
        self.assertEqual(check["status"], "pass")
        self.assertEqual(len(check["evidence"]["comparisons"]), 2)

    def test_spacing_is_unavailable_for_ambiguous_layouts(self):
        for kwargs in ({"tables": True}, {"column_candidate": True}, {"rotated": True}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.spacing_result([], **kwargs)["section_spacing"]["status"], "unavailable")
        self.assertEqual(spacing_checks({"status": "unavailable"}, self.policy)[0]["status"], "unavailable")

    def test_insufficient_spacing_samples_are_not_a_pass(self):
        result = self.spacing_result([self.line("Projects", 10, 0), self.line("- Built an app", 30, 1)])
        self.assertEqual(result["section_spacing"]["status"], "not_applicable")
        self.assertEqual(result["paragraph_spacing"]["status"], "not_applicable")

    def test_pdf_spacing_analysis_and_explicit_scope(self):
        with fitz.open() as doc:
            page = doc.new_page()
            for index, (heading, y) in enumerate(zip(("Skills", "Education", "Experience", "Projects"), (40, 120, 200, 360))):
                page.insert_text((40, y), heading, fontname="hebo", fontsize=11)
                page.insert_text((40, y + 22), "Readable section content.", fontsize=11)
            doc.save(self.path)
        result = score_resume_format({"full_resume_text": RESUME}, file_path=self.path)
        self.assertEqual(self.rule(result, "section_spacing")["status"], "warning")
        self.assertEqual(result["not_implemented_checks"], [])
        self.assertIn("Weighted", result["status_scope"])
        json.dumps(result, allow_nan=False)

    def test_invalid_analysis_policy_is_rejected(self):
        for kwargs in ({"divider_max_thickness_pt": float("nan")}, {"divider_min_aspect_ratio": 0},
                       {"spacing_min_samples": 0}, {"spacing_relative_tolerance": float("inf")},
                       {"spelling_allowed_words": "developd"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ScoringPolicy(**kwargs)


if __name__ == "__main__":
    unittest.main()
