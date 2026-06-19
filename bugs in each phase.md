# ApplyWise Bug Breakdown By Phase

This file tracks the known bugs, incomplete implementations, and production-level fixes that still need to be completed across the three backend phases.

Status meaning:
- `Bug`: existing behavior is incorrect, brittle, or misleading
- `Incomplete`: logic exists but is too shallow for production
- `Production Change`: hardening work needed so many users can rely on the product

---

## Phase 1: Resume Parsing

### 1. Section detection is too naive
- Type: `Bug`
- Current behavior:
  - Checks whether words like `experience`, `skills`, or `education` appear anywhere in the text.
- Why this is a problem:
  - False positives happen when those words appear in sentences but not as real sections.
  - Resumes using `Work History`, `Professional Experience`, `Core Competencies`, or similar headings get missed.
- How to solve it:
  - Parse line by line instead of only scanning the full blob.
  - Create a section-heading alias map.
  - Detect headings using short-line patterns, layout cues, and heading normalization.
  - Attach content blocks to the detected heading.

### 2. Bullet detection is unreliable
- Type: `Bug`
- Current behavior:
  - Bullet detection depends on garbled encoded characters and a few plain symbols.
- Why this is a problem:
  - Good resumes can be marked as having no bullets.
  - Text extraction encoding differences break the check.
- How to solve it:
  - Normalize bullet-like unicode characters into one internal marker.
  - Detect bullets by line starts, not by raw character presence only.
  - Support numbered bullets, dash bullets, and common PDF extraction bullet symbols.

### 3. Phone parsing is too limited
- Type: `Bug`
- Current behavior:
  - Regex only handles a narrow set of phone formats.
- Why this is a problem:
  - International numbers and alternate formatting get missed.
  - Some valid resumes look incomplete.
- How to solve it:
  - Replace with broader digit-group parsing.
  - Validate likely phone candidates using total digit count and separator patterns.
  - Support country code, spaces, brackets, hyphens, and local variants.

### 4. Contact placement check is weak
- Type: `Bug`
- Current behavior:
  - Uses a narrow email/10-digit number search in page blocks.
- Why this is a problem:
  - Misses many valid phone formats.
  - Can match unrelated numbers.
  - Penalizes header placement too aggressively.
- How to solve it:
  - Reuse the improved contact extractor for placement checks.
  - Treat header/footer contact as a risk signal, not an automatic strong penalty.
  - Only flag when extraction quality is also weak.

### 5. Multi-column detection is too crude
- Type: `Bug`
- Current behavior:
  - Uses x-position spread only.
- Why this is a problem:
  - Can falsely mark normal layouts as multi-column.
  - Does not measure whether reading order is actually broken.
- How to solve it:
  - Inspect block reading order page by page.
  - Detect actual left-right text stream jumping.
  - Flag only when the extraction order appears risky.

### 6. Font inconsistency logic is incomplete
- Type: `Bug`
- Current behavior:
  - Collects font sizes and families, but does not use the data well.
- Why this is a problem:
  - Counts noise but does not produce meaningful hierarchy checks.
- How to solve it:
  - Add font-family count thresholds.
  - Add heading/body size hierarchy checks.
  - Detect outlier fonts and outlier font sizes.

### 7. Parser assumes extracted text is always usable
- Type: `Incomplete`
- Current behavior:
  - Resume text is extracted and immediately trusted.
- Why this is a problem:
  - Scanned PDFs, broken PDFs, or poor extraction lead to misleading scores.
- How to solve it:
  - Add parser confidence scoring.
  - Measure word count, character count, weird-character ratio, line fragmentation, and empty pages.
  - Warn users when parsing quality is poor.

### 8. No scanned/image-only PDF detection
- Type: `Incomplete`
- Current behavior:
  - Image-only PDFs are likely to produce very little text and then receive bad ATS scores.
- Why this is a problem:
  - The user is blamed for a parser limitation.
- How to solve it:
  - Add scanned-PDF heuristics.
  - If text extraction is too low but images/pages exist, warn that OCR or text-based export is needed.

### 9. Text normalization is too weak
- Type: `Incomplete`
- Current behavior:
  - Only compresses whitespace and lowercases text.
- Why this is a problem:
  - OCR junk, ligatures, broken bullets, strange separators, and unicode noise remain.
- How to solve it:
  - Add normalization for bullets, ligatures, punctuation, repeated blank lines, unicode dashes, and extracted glyph junk.

### 10. Parsing is not structured
- Type: `Incomplete`
- Current behavior:
  - Most scoring logic runs on a single cleaned text blob.
- Why this is a problem:
  - Hard to trust and hard to explain.
  - Makes Phase 2 and Phase 3 weaker.
- How to solve it:
  - Build a parsed resume object with:
    - contact info
    - sections
    - section content
    - detected links
    - extracted skills
    - parsing warnings
    - layout risks

### 11. No link extraction
- Type: `Incomplete`
- Current behavior:
  - No parsing for LinkedIn, GitHub, portfolio, or personal site.
- Why this is a problem:
  - Important role-specific resume signals are ignored.
- How to solve it:
  - Add regex/entity extraction for professional links.
  - Normalize URLs and plain-text domain variants.

### 12. Missing-section logic is too rigid
- Type: `Incomplete`
- Current behavior:
  - Always expects `experience`, `education`, and `skills` exact strings.
- Why this is a problem:
  - Penalizes valid section naming variations.
- How to solve it:
  - Use canonical section names and alias mapping.
  - Distinguish between missing, weak, and unclear sections.

### 13. Word-count logic is too simplistic
- Type: `Incomplete`
- Current behavior:
  - Short and long resumes are judged mainly by word count thresholds.
- Why this is a problem:
  - Freshers and senior candidates get treated unfairly.
- How to solve it:
  - Replace with usable-content checks, section density, and evidence richness.

### 14. No extraction confidence per entity
- Type: `Incomplete`
- Current behavior:
  - Features are booleans only.
- Why this is a problem:
  - Missing can mean absent or poorly parsed.
- How to solve it:
  - Add confidence per entity and per section.

### 15. Backend upload validation is too weak
- Type: `Production Change`
- Current behavior:
  - Backend trusts uploaded content too much.
- Why this is a problem:
  - Broken files, empty files, wrong file types, and oversize uploads can cause failures or misleading results.
- How to solve it:
  - Add backend file extension, MIME type, empty payload, and file-size validation.

### 16. No explicit parsing failure states
- Type: `Production Change`
- Current behavior:
  - Failures may surface as generic errors or poor results.
- Why this is a problem:
  - Bad production UX and weak debugging.
- How to solve it:
  - Return parsing-specific errors such as unreadable PDF, scanned PDF likely, corrupted file, and no usable text extracted.

### 17. No safe parsing instrumentation
- Type: `Production Change`
- Current behavior:
  - No timing, observability, or parsing diagnostics.
- Why this is a problem:
  - Hard to debug production failures at scale.
- How to solve it:
  - Add logs for extraction success, parse warnings, and failure category without storing raw resume text.

---

## Phase 2: Comparison Between Resume and JD

### 1. Matching is still mostly direct string matching
- Type: `Bug`
- Current behavior:
  - Taxonomy terms are matched by substring presence in normalized text.
- Why this is a problem:
  - Context is ignored.
  - One weak mention looks as strong as real evidence.
- How to solve it:
  - Move to evidence-aware matching.
  - Score term presence based on where it appears: skills section, projects, or experience.
  - Add lemmatization and fuzzy normalization.

### 2. All JD terms are treated equally
- Type: `Bug`
- Current behavior:
  - Required skills and optional skills influence score the same way.
- Why this is a problem:
  - The score can hide major mismatches.
- How to solve it:
  - Split JD into required, preferred, responsibilities, education, certifications, and tools.
  - Weight required qualifications more heavily.

### 3. JD noise is not filtered
- Type: `Bug`
- Current behavior:
  - Company fluff and non-requirement text can affect extracted terms.
- Why this is a problem:
  - Matching becomes noisy and unfair.
- How to solve it:
  - Remove company description, benefits, culture text, and equal-opportunity blocks before matching.

### 4. Keyword score can be misleading
- Type: `Bug`
- Current behavior:
  - Score is a flat percentage of matched taxonomy terms.
- Why this is a problem:
  - Missing a critical requirement may still yield a decent score.
- How to solve it:
  - Produce category-wise scores and a critical-gap list.

### 5. No evidence weighting for matched terms
- Type: `Bug`
- Current behavior:
  - A single term mention counts as a match.
- Why this is a problem:
  - Encourages weak keyword presence rather than real role evidence.
- How to solve it:
  - Add weighted evidence levels:
    - skills section
    - project evidence
    - work experience evidence
    - repeated validated mentions

### 6. JD is not segmented into requirement groups
- Type: `Incomplete`
- Current behavior:
  - All detected terms go into one pool.
- Why this is a problem:
  - No clear understanding of what the job actually demands.
- How to solve it:
  - Parse JD into:
    - required skills
    - preferred skills
    - tools/platforms
    - certifications
    - education
    - responsibilities

### 7. No years-of-experience comparison
- Type: `Incomplete`
- Current behavior:
  - JD years and resume years are not compared.
- Why this is a problem:
  - One of the strongest hiring filters is completely missing.
- How to solve it:
  - Extract experience requirements from JD.
  - Estimate total experience from resume dates and later from user input.

### 8. No seniority or role extraction from JD
- Type: `Incomplete`
- Current behavior:
  - Comparison is not role-aware.
- Why this is a problem:
  - Data analyst, ML engineer, and backend developer should not be compared the same way.
- How to solve it:
  - Detect role title, seniority level, and domain terms from JD.

### 9. No domain-aware matching
- Type: `Incomplete`
- Current behavior:
  - Terms are matched without understanding industry context.
- Why this is a problem:
  - A resume can be technically strong but misaligned to the domain.
- How to solve it:
  - Add domain vocab groups and domain-fit scoring.

### 10. No education and certification comparison
- Type: `Incomplete`
- Current behavior:
  - These are not compared in a structured way against JD requirements.
- Why this is a problem:
  - Major hiring filters are ignored.
- How to solve it:
  - Extract education/certification requirements from JD and compare with parsed resume entities.

### 11. No confidence-aware missing-term logic
- Type: `Incomplete`
- Current behavior:
  - Missing terms are treated as definitely absent.
- Why this is a problem:
  - Low parser quality can create false misses.
- How to solve it:
  - Downgrade confidence of missing-term deductions when parsing confidence is low.

### 12. No production-safe taxonomy expansion workflow
- Type: `Production Change`
- Current behavior:
  - Taxonomy is static and manually expanded.
- Why this is a problem:
  - Hard to maintain as the product scales across roles and industries.
- How to solve it:
  - Move taxonomy to structured data files and version it.
  - Track additions by category and regression-test them.

### 13. No benchmarked comparison quality
- Type: `Production Change`
- Current behavior:
  - Comparison logic is not calibrated against labeled examples.
- Why this is a problem:
  - Scores may look scientific but are not validated.
- How to solve it:
  - Build a labeled evaluation set of resumes and JDs.
  - Measure match precision, recall, and false positives.

---

## Phase 3: Result Analysis and Report Generation

### 1. Results are too shallow
- Type: `Bug`
- Current behavior:
  - Output is mainly scores plus simple lists.
- Why this is a problem:
  - Users cannot clearly understand what to fix first.
- How to solve it:
  - Return structured findings with category, severity, reason, and fix.

### 2. No reason attached to deductions
- Type: `Bug`
- Current behavior:
  - Scores drop but there is not enough explanation.
- Why this is a problem:
  - Low trust and poor product clarity.
- How to solve it:
  - Every deduction should include evidence and recommended action.

### 3. Final score is over-confident
- Type: `Bug`
- Current behavior:
  - The final score looks precise even when parser quality or JD matching is weak.
- Why this is a problem:
  - Can mislead users.
- How to solve it:
  - Add score confidence or confidence warnings.
  - Make parser quality influence how results are presented.

### 4. Output mixes issue types together
- Type: `Bug`
- Current behavior:
  - Format issues, content gaps, and JD mismatches are not separated enough.
- Why this is a problem:
  - Hard for users to prioritize fixes.
- How to solve it:
  - Split the report into:
    - parsing issues
    - ATS format issues
    - resume content issues
    - JD comparison issues
    - suggested improvements

### 5. No severity labels
- Type: `Bug`
- Current behavior:
  - All issues look equally important.
- Why this is a problem:
  - A critical ATS blocker and a small optimization look the same.
- How to solve it:
  - Add severity levels like critical, high, medium, and low.

### 6. No structured issue schema
- Type: `Incomplete`
- Current behavior:
  - Issues are plain strings.
- Why this is a problem:
  - Hard to render well in frontend and hard to evolve the API.
- How to solve it:
  - Return issue objects with:
    - id
    - category
    - severity
    - title
    - explanation
    - evidence
    - fix

### 7. No prioritized fix order
- Type: `Incomplete`
- Current behavior:
  - User receives a flat list of problems.
- Why this is a problem:
  - No guidance on what matters most.
- How to solve it:
  - Sort issues by severity and estimated score impact.
  - Group into fix-now, improve-next, and optional.

### 8. No score explanation layer
- Type: `Incomplete`
- Current behavior:
  - Score breakdown is minimal.
- Why this is a problem:
  - Users do not know what content, format, and JD scores actually mean.
- How to solve it:
  - Explain each score component in product language.

### 9. No parser-quality messaging in report
- Type: `Incomplete`
- Current behavior:
  - Weak parsing can silently affect all later results.
- Why this is a problem:
  - Creates false confidence.
- How to solve it:
  - Surface parser-confidence warnings at the top of the report.

### 10. No role-aware reporting
- Type: `Incomplete`
- Current behavior:
  - Reports are generic.
- Why this is a problem:
  - The best next action differs by role and seniority.
- How to solve it:
  - Tailor suggestions by role family and candidate level.

### 11. API response is too thin for a production SaaS
- Type: `Production Change`
- Current behavior:
  - Returns only a few primitive fields.
- Why this is a problem:
  - Limits frontend, analytics, history, and future explainability.
- How to solve it:
  - Expand response schema with structured findings, parsing diagnostics, category-wise match data, and confidence fields.

### 12. No reporting analytics and versioning
- Type: `Production Change`
- Current behavior:
  - No schema versioning or reporting telemetry.
- Why this is a problem:
  - Hard to safely evolve the report format.
- How to solve it:
  - Add schema version and log issue-category frequencies for product improvement.

---

## Cross-Phase Dependencies

### Phase 1 blocks Phase 2
- If parsing is weak, JD matching becomes unreliable.

### Phase 2 blocks Phase 3 quality
- If JD comparison is shallow, the report cannot explain real fit properly.

### Phase 3 should not hide Phase 1 uncertainty
- Report generation must surface low parser confidence instead of pretending the score is certain.

---

## Recommended Completion Order

1. Phase 1 parsing quality, normalization, and section detection
2. Phase 1 structured parsed resume object
3. Phase 2 JD segmentation and weighted matching
4. Phase 2 experience, education, and certification comparison
5. Phase 3 structured issue schema
6. Phase 3 prioritized and confidence-aware reporting
