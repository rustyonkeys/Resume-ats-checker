import json
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

import fitz

from Backend.services.scoring import ScoringPolicy, score_resume_format
from Backend.services.scoring.document_features import extract_features
from Backend.services.scoring.layout_analyzer import analyze_pdf_layout, font_family


RESUME = "\n".join([
    "Alex Student",
    "alex@example.com | +91 98765 43210",
    "EDUCATION",
    "Bachelor of Science in Computer Science, University of Example, 2022 - 2026",
    "Technical Skills: Python, SQL, Git, testing, accessibility, documentation",
    "ACADEMIC PROJECTS",
] + [
    "- Built reliable Python services with clear tests and useful documentation.",
    "- Tested input validation against realistic files and malformed documents.",
    "- Improved application usability based on feedback from student volunteers.",
    "- Documented setup steps and maintained examples for future contributors.",
    "- Added meaningful integration tests for upload and extraction workflows.",
    "- Reviewed output accuracy with annotated examples and recorded failures.",
    "- Designed accessible forms with readable labels and helpful error messages.",
    "- Measured response times and reduced repeated work during document analysis.",
    "- Organized tasks and reviewed changes with peers throughout the project.",
    "- Compared extracted content against source documents to identify missing text.",
    "- Created reproducible examples for difficult layouts and unusual characters.",
    "- Maintained configuration files and detailed release notes for each version.",
    "- Collaborated with classmates to evaluate usability and resolve reported issues.",
])


class FormatScoringTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).resolve().parent / f"fixture_{uuid4().hex}.pdf"
        self.addCleanup(self.path.unlink, missing_ok=True)

    def make_pdf(self, text=RESUME, fontsize=11, blank_page=False):
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_text((45, 40), text, fontsize=fontsize)
            if blank_page:
                doc.new_page()
            doc.save(self.path)
        return self.path

    def score(self, text=RESUME, path=None, **kwargs):
        return score_resume_format({"valid": True, "full_resume_text": text,
                                    "page_count": 1, "extension": ".pdf"},
                                   [{"index": 0, "category": "Text", "text": text}],
                                   path, **kwargs)

    @staticmethod
    def rule(result, rule_id):
        return next(check for component in result["breakdown"].values()
                    for check in component["checks"] if check["rule_id"] == rule_id)

    def test_fresher_projects_can_earn_full_score_without_experience_or_links(self):
        result = self.score(path=self.make_pdf())
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["coverage_percentage"], 100)
        self.assertEqual(self.rule(result, "projects_or_experience")["score"], 3)
        self.assertNotIn("spelling", result["unavailable_checks"])
        self.assertEqual(result["not_implemented_checks"], [])
        self.assertEqual(self.rule(result, "ocr")["status"], "not_applicable")
        json.dumps(result, allow_nan=False)

    def test_deterministic_and_does_not_mutate_input(self):
        validation = {"full_resume_text": RESUME, "page_count": 1}
        blocks = [{"text": RESUME}]
        before = json.dumps([validation, blocks])
        first = score_resume_format(validation, blocks)
        self.assertEqual(first, score_resume_format(validation, blocks))
        self.assertEqual(before, json.dumps([validation, blocks]))

    def test_missing_pdf_never_becomes_a_full_score(self):
        result = self.score()
        self.assertEqual(result["status"], "partial")
        self.assertIsNone(result["score"])
        self.assertIsNone(result["percentage"])
        self.assertLess(result["coverage_percentage"], 100)
        self.assertEqual(self.rule(result, "tables")["status"], "unavailable")

    def test_empty_or_symbols_only_text_is_unscorable(self):
        for text in ("", "  \n\t", "----- ***"):
            with self.subTest(text=text):
                result = self.score(text)
                self.assertEqual(result["status"], "unscorable")
                self.assertIsNone(result["score"])
                self.assertIsNone(result["provisional_percentage"])

    def test_heading_matching_is_case_insensitive_and_supports_inline_content(self):
        features = extract_features("TECHNICAL SKILLS: Python\nEDUCATION\nBSc\nAcademic Projects\n- Built an app")
        self.assertEqual([s["type"] for s in features["sections"]], ["skills", "education", "projects"])
        self.assertEqual(features["sections"][0]["lines"][0]["text"], "Python")

    def test_prose_substrings_do_not_count_as_headings(self):
        features = extract_features("I have experience with education software and skills training.")
        self.assertEqual(features["sections"], [])

    def test_skill_subsections_remain_under_skills(self):
        text = ("Technical Skills\nLanguages: Python, R, SQL\n"
                "Technologies: Git, Docker\nData Science: Machine Learning\n"
                "Experience\n- Built a service")
        result = self.score(text)
        sections = result["features"]["sections"]
        self.assertEqual([s["type"] for s in sections], ["skills", "experience"])
        self.assertEqual([line["text"] for line in sections[0]["lines"]], text.splitlines()[1:4])
        self.assertEqual(self.rule(result, "skills")["score"], 2)

    def test_standalone_languages_still_starts_a_separate_section(self):
        text = "Skills\nPython, SQL\nLanguages\nEnglish, Hindi\nEducation\nBSc"
        sections = extract_features(text)["sections"]
        self.assertEqual([s["type"] for s in sections], ["skills", "other", "education"])
        self.assertEqual(len(sections[0]["lines"]), 1)

    def test_languages_outside_skills_is_not_a_skill_subsection(self):
        sections = extract_features("Education\nBSc\nLanguages: English, Hindi")["sections"]
        self.assertEqual([s["type"] for s in sections], ["education", "other"])

    def test_empty_skill_subsection_labels_are_not_content(self):
        result = self.score("Technical Skills\nLanguages:\nTools:\nEducation\nBSc")
        self.assertEqual(self.rule(result, "skills")["score"], 0)
        result = self.score("Technical Skills\nLanguages:\nPython, SQL\nEducation\nBSc")
        self.assertEqual(self.rule(result, "skills")["score"], 2)

    def test_invisible_characters_in_bullets_do_not_change_source_lines(self):
        for marker in ("\u2022\u200b ", "\ufeff\u2022\u200b", "-\u2060 ", "1.\u200b "):
            with self.subTest(marker=marker):
                line = marker + "Built a tested service"
                result = self.score("Projects\n" + line)
                self.assertEqual(result["features"]["line_analysis"]["bullet_lines"], 1)
                self.assertEqual(self.rule(result, "achievement_bullets")["deduction"], 0)
                self.assertEqual(result["features"]["lines"][1]["text"], line)
                self.assertEqual(result["features"]["sections"][0]["lines"][0]["text"], line)

    def test_invisible_only_bullets_and_hyphenated_words_do_not_match(self):
        for line in ("\u2022\u200b ", "-\u200btested", "2022-\u200b2023", "well-\u200btested"):
            with self.subTest(line=line):
                self.assertEqual(extract_features(line)["line_analysis"]["bullet_lines"], 0)

    def test_pdf_annotations_merge_with_text_urls_across_pages(self):
        with fitz.open() as doc:
            for _ in range(2):
                page = doc.new_page()
                page.insert_text((40, 40), "LinkedIn | GitHub | Project")
                for i, uri in enumerate(("https://github.com/example", "https://www.linkedin.com/in/example",
                                         "https://EXAMPLE.com:443", "mailto:person@example.com")):
                    page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(40, 60 + i * 20, 140, 75 + i * 20),
                                      "uri": uri})
                page.insert_link({"kind": fitz.LINK_GOTO, "from": fitz.Rect(40, 180, 140, 195),
                                  "page": 0, "to": fitz.Point(0, 0)})
            doc.save(self.path)
        result = self.score(RESUME + "\nhttps://example.com/\ngithub.com/example", self.path)
        self.assertEqual(result["features"]["contact_info"]["links"], [
            "https://example.com/", "https://github.com/example", "https://www.linkedin.com/in/example"])
        self.assertEqual(self.rule(result, "contact_method")["evidence"]["link_count"], 3)
        self.assertEqual(len(result["layout"]["pages"][0]["links"]), 4)
        json.dumps(result, allow_nan=False)

    def test_url_deduplication_preserves_path_case_queries_and_fragments(self):
        links = extract_features("https://example.com/Repo?x=1#readme", embedded_links=[
            "https://EXAMPLE.COM:443/Repo?x=1#readme", "https://example.com/repo?x=1#readme",
            "https://example.com/Repo?x=2#readme", "https://example.com/Repo?x=1#usage",
            "https://example.com/wiki/Function_(math)"])["contact_info"]["links"]
        self.assertEqual(len(links), 5)
        self.assertIn("https://example.com/wiki/Function_(math)", links)

    def test_invalid_and_non_web_annotation_targets_are_excluded(self):
        links = extract_features("", embedded_links=[
            "mailto:person@example.com", "file:///local.pdf", "javascript:alert(1)",
            "https://", "https://[invalid", "https://example.com:bad", "https://example.com/a b",
            "https://user:pass@example.com", None, "https://example.com/portfolio"])["contact_info"]["links"]
        self.assertEqual(links, ["https://example.com/portfolio"])

    def test_annotation_failure_keeps_text_links_and_other_analysis(self):
        path = self.make_pdf()
        with patch.object(fitz.Page, "get_links", side_effect=RuntimeError("unavailable")):
            result = self.score(RESUME + "\nhttps://example.com/", path)
        self.assertEqual(result["layout"]["status"], "ok")
        self.assertIsNone(result["layout"]["pages"][0]["links"])
        self.assertEqual(result["features"]["contact_info"]["links"], ["https://example.com/"])
        self.assertEqual(result["layout"]["errors"][0]["check"], "links")

    def test_missing_pdf_preserves_text_links(self):
        result = self.score(RESUME + "\nhttps://github.com/example")
        self.assertEqual(result["features"]["contact_info"]["links"], ["https://github.com/example"])

    def test_skills_and_bullet_regression_in_combined_score(self):
        text = RESUME.replace("Technical Skills: Python, SQL, Git, testing, accessibility, documentation",
                              "Technical Skills\nLanguages: Python, SQL\nTools: Git, testing")
        text = text.replace("- ", "\u2022\u200b ")
        result = self.score(text, self.make_pdf(text))
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["rule_version"], "format-v1.3")
        self.assertEqual(result["features"]["line_analysis"]["bullet_lines"], 13)

    def test_empty_headings_do_not_earn_section_points(self):
        result = self.score("Education\nSkills\nProjects\n")
        self.assertEqual(result["breakdown"]["section_structure"]["score"], 0)

    def test_custom_or_unsupported_language_headings_are_not_invented(self):
        result = self.score("Formation\nLicence informatique\nComp\u00e9tences\nPython", language="fr")
        self.assertEqual(result["breakdown"]["section_structure"]["assessed_max_score"], 0)
        self.assertEqual(self.rule(result, "education")["status"], "unavailable")

    def test_hyphens_in_prose_are_not_bullets(self):
        result = self.score("Projects\nBuilt a well-tested tool in 2022-2023.")
        self.assertEqual(result["features"]["line_analysis"]["bullet_lines"], 0)
        self.assertEqual(self.rule(result, "achievement_bullets")["deduction"], 1)

    def test_common_bullets_and_numbered_items(self):
        features = extract_features("\u2022 Built a tool\n- Tested a tool\n1. Released a tool\n* Documented a tool")
        self.assertEqual(features["line_analysis"]["bullet_lines"], 4)

    def test_wrapped_long_bullet_is_advisory(self):
        result = self.score("Projects\n- Built a tool\n" + "extra " * 60)
        rule = self.rule(result, "long_bullets")
        self.assertEqual(rule["status"], "warning")
        self.assertEqual(rule["deduction"], 0)

    def test_email_and_international_phone_candidates(self):
        features = extract_features("Person.Name+jobs@example.co.uk\n+44 (20) 7946 0958\n2019 - 2023\n2024-06-15")
        self.assertEqual(features["contact_info"]["emails"], ["Person.Name+jobs@example.co.uk"])
        self.assertEqual(features["contact_info"]["phones"], ["+44 (20) 7946 0958"])

    def test_phone_alone_is_a_contact_method(self):
        self.assertEqual(self.rule(self.score("Phone: +91 98765 43210"), "contact_method")["score"], 5)

    def test_top_of_page_contact_is_not_penalized(self):
        result = self.score(path=self.make_pdf())
        self.assertEqual(self.rule(result, "contact_method")["score"], 5)

    def test_unicode_names_and_technical_words_are_not_typos(self):
        result = self.score("Jos\u00e9 \u674e\u660e C++ Kubernetes PyTorch na\u00efve")
        self.assertEqual(self.rule(result, "encoding_noise")["deduction"], 0)
        self.assertEqual(self.rule(result, "spelling")["status"], "not_applicable")

    def test_encoding_noise_is_only_deducted_once(self):
        path = self.make_pdf()
        result = self.score(RESUME + "\ufffd", path)
        self.assertEqual(result["breakdown"]["parse_quality"]["score"], 8)
        self.assertEqual(self.rule(result, "encoding_noise")["deduction"], 1)
        self.assertEqual(result["score"], 39)

    def test_blank_page_is_reported_and_pdf_page_count_is_authoritative(self):
        result = self.score(path=self.make_pdf(blank_page=True))
        coverage = self.rule(result, "page_text_coverage")
        self.assertEqual(coverage["evidence"]["pages_without_text"], [2])
        self.assertEqual(coverage["deduction"], 2)
        self.assertEqual(self.rule(result, "page_count")["evidence"]["page_count"], 2)

    def test_small_body_font_has_evidence(self):
        result = self.score(path=self.make_pdf(fontsize=7))
        self.assertEqual(self.rule(result, "small_body_text")["deduction"], 2)

    def test_font_variants_do_not_inflate_family_count(self):
        for name in ("ABCDEF+Arial-BoldMT", "Arial-ItalicMT", "ArialMT"):
            self.assertEqual(font_family(name), "arialmt")
        with fitz.open() as doc:
            page = doc.new_page()
            for i, font in enumerate(("helv", "hebo", "heit", "hebi")):
                page.insert_text((40, 40 + 20 * i), "Readable sample text", fontname=font)
            doc.save(self.path)
        self.assertEqual(len(analyze_pdf_layout(self.path)["font_families"]), 1)

    def test_right_aligned_dates_are_not_columns(self):
        with fitz.open() as doc:
            page = doc.new_page()
            for i in range(8):
                y = 60 + i * 30
                page.insert_text((40, y), "Worked on an application")
                page.insert_text((460, y), "2022 - 2023")
            doc.save(self.path)
        self.assertIsNone(analyze_pdf_layout(self.path)["pages"][0]["column_candidate"])

    def test_substantial_columns_are_advisory(self):
        with fitz.open() as doc:
            page = doc.new_page()
            for i in range(8):
                y = 60 + i * 30
                page.insert_text((40, y), "Built a useful application")
                page.insert_text((340, y), "Tested many realistic inputs")
            doc.save(self.path)
        result = self.score(path=self.path)
        self.assertEqual(self.rule(result, "columns")["status"], "warning")
        self.assertEqual(self.rule(result, "columns")["deduction"], 0)

    def test_table_detection_and_no_automatic_table_penalty(self):
        with fitz.open() as doc:
            page = doc.new_page()
            for x in (40, 200, 360):
                page.draw_line((x, 60), (x, 150))
            for y in (60, 90, 120, 150):
                page.draw_line((40, y), (360, y))
            for row in range(3):
                page.insert_text((50, 80 + row * 30), "Skill")
                page.insert_text((210, 80 + row * 30), "Python")
            doc.save(self.path)
        result = self.score(path=self.path)
        self.assertEqual(self.rule(result, "tables")["status"], "warning")
        self.assertEqual(self.rule(result, "tables")["deduction"], 0)

    def test_table_detector_failure_is_not_a_pass(self):
        path = self.make_pdf()
        with patch.object(fitz.Page, "find_tables", side_effect=RuntimeError("unavailable")):
            result = self.score(path=path)
        self.assertEqual(self.rule(result, "tables")["status"], "unavailable")
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["layout"]["errors"])

    def test_docx_has_explicit_partial_analysis(self):
        result = self.score(path=self.path.with_suffix(".docx"))
        self.assertEqual(result["status"], "partial")
        self.assertIn("PDF only", result["layout"]["reason"])

    def test_missing_or_corrupt_pdf_is_reported(self):
        self.assertEqual(analyze_pdf_layout(self.path)["status"], "unavailable")
        self.path.write_bytes(b"not a PDF")
        result = self.score(path=self.path)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["layout"]["errors"])

    def test_analysis_page_limit_is_explicit(self):
        path = self.make_pdf(blank_page=True)
        result = self.score(path=path, policy=ScoringPolicy(max_analysis_pages=1))
        self.assertEqual(result["layout"]["status"], "unavailable")
        self.assertIn("page limit", result["layout"]["reason"])

    def test_policy_is_configurable_and_scores_remain_bounded(self):
        result = self.score(path=self.make_pdf(), policy=ScoringPolicy(min_words=300))
        self.assertEqual(self.rule(result, "word_count")["deduction"], 1)
        for component in result["breakdown"].values():
            self.assertLessEqual(0, component["score"])
            self.assertLessEqual(component["score"], component["assessed_max_score"])
            self.assertLessEqual(component["assessed_max_score"], component["max_score"])
        self.assertEqual(sum(c["max_score"] for c in result["breakdown"].values()), 40)

    def test_invalid_inputs_fail_clearly(self):
        for validation in ({}, {"full_resume_text": None}, {"full_resume_text": RESUME, "valid": False}):
            with self.subTest(validation=validation), self.assertRaises(ValueError):
                score_resume_format(validation)
        with self.assertRaises(TypeError):
            score_resume_format({"full_resume_text": RESUME}, {"blocks": []})
        with self.assertRaises(ValueError):
            self.score(policy=ScoringPolicy(max_text_chars=20))
        for kwargs in ({"min_words": 2000}, {"max_pages": 0}, {"noise_fraction": float("nan")}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ScoringPolicy(**kwargs)


if __name__ == "__main__":
    unittest.main()
