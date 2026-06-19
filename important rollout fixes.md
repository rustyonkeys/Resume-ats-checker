# ApplyWise Rollout Fixes

This file is a launch-focused filter over the larger bug backlog.

Goal:
- fix only the issues that are necessary for the app to work reliably enough for rollout
- separate true launch blockers from improvements that can wait until after users start using the product

Important note:
- this file is intentionally stricter and smaller than `bugs in each phase.md`
- if an item affects parsing trust, JD comparison correctness, or score credibility, it belongs in the first section

---

## 1. Important And Necessary Fixes

These are the issues that should be fixed before rolling out the app if you want the product to work properly and not mislead users.

### Phase 1: Resume Parsing

#### 1. Backend file validation is too weak
- Why it is important:
  - bad files, empty files, wrong file types, and oversized uploads can break the analysis flow or produce misleading results
- What must be fixed:
  - validate PDF type on backend
  - reject empty files
  - reject corrupted/unreadable files safely
  - enforce file-size limits on backend

#### 2. Parser assumes extracted text is always usable
- Why it is important:
  - if text extraction is weak, every later phase becomes unreliable
- What must be fixed:
  - add parser confidence checks
  - detect very low extracted text
  - detect fragmented extraction
  - warn when results are low-confidence

#### 3. No scanned/image-only PDF detection
- Why it is important:
  - image PDFs will be scored badly even when the resume itself is fine
- What must be fixed:
  - detect likely scanned PDFs
  - return a warning like “resume is not text-readable, please upload a text-based PDF”

#### 4. Section detection is too naive
- Why it is important:
  - current parsing can incorrectly say sections exist or are missing
- What must be fixed:
  - replace exact word checks with heading-based section detection
  - support aliases like `professional experience`, `work history`, `technical skills`, `core competencies`

#### 5. Text normalization is too weak
- Why it is important:
  - unicode junk, broken bullets, weird separators, and OCR noise reduce parsing quality
- What must be fixed:
  - normalize bullets
  - normalize unicode punctuation
  - normalize repeated spaces and broken line patterns

#### 6. Bullet detection is unreliable
- Why it is important:
  - good resumes can be flagged incorrectly and lose score unfairly
- What must be fixed:
  - bullet detection should use normalized lines and multiple bullet patterns

#### 7. Phone parsing is too limited
- Why it is important:
  - contact information is a core ATS check
- What must be fixed:
  - broaden phone parsing to support real-world valid formats

#### 8. Multi-column detection is too crude
- Why it is important:
  - your app may falsely punish valid resumes
- What must be fixed:
  - detect reading-order risk instead of only wide x-position spread

#### 9. Parsing is not structured
- Why it is important:
  - scoring and JD comparison are still relying too much on one text blob
- What must be fixed:
  - create a structured parsed resume object with sections, contact info, links, and parsing warnings

---

### Phase 2: Comparison Between Resume And JD

#### 10. Matching is still mostly direct string matching
- Why it is important:
  - comparison quality will look shallow and inaccurate
- What must be fixed:
  - move from plain presence matching to evidence-aware matching
  - recognize whether a skill is just named once or actually supported by projects/experience

#### 11. All JD terms are treated equally
- Why it is important:
  - critical requirements and optional requirements should not affect the score in the same way
- What must be fixed:
  - split required vs preferred requirements
  - weight required items more heavily

#### 12. JD noise is not filtered
- Why it is important:
  - company fluff can pollute matching and lower trust
- What must be fixed:
  - remove benefits, company-description, and non-requirement boilerplate from JD before matching

#### 13. Keyword score can be misleading
- Why it is important:
  - users may trust a score that hides important missing qualifications
- What must be fixed:
  - create category-wise matching instead of one flat match score
  - surface critical missing terms separately

#### 14. No JD segmentation into requirement groups
- Why it is important:
  - proper comparison is impossible without understanding what the JD is asking for
- What must be fixed:
  - split JD into skills, tools, education, certifications, responsibilities, and preferred items

#### 15. No years-of-experience comparison
- Why it is important:
  - this is one of the most common recruiter filters
- What must be fixed:
  - extract years required from JD
  - estimate experience from resume or user input

#### 16. No education and certification comparison
- Why it is important:
  - major hiring filters are being ignored
- What must be fixed:
  - compare parsed education and certifications with JD requirements

---

### Phase 3: Result Analysis And Scoring

#### 17. Final score is over-confident
- Why it is important:
  - users may think the score is more trustworthy than it really is
- What must be fixed:
  - make parser confidence influence reporting
  - reduce confidence when parsing is weak

#### 18. Results are too shallow
- Why it is important:
  - users need to know exactly what is wrong and what to do next
- What must be fixed:
  - return structured findings, not just score + simple issue strings

#### 19. No reason attached to deductions
- Why it is important:
  - weak explanation reduces trust and product usefulness
- What must be fixed:
  - every deduction should include:
    - reason
    - evidence
    - recommendation

#### 20. No severity labels
- Why it is important:
  - launch users must know what to fix first
- What must be fixed:
  - classify findings as critical, high, medium, or low

#### 21. Output mixes issue types together
- Why it is important:
  - users cannot tell whether the problem is parsing, ATS formatting, or JD mismatch
- What must be fixed:
  - split results into parsing issues, ATS format issues, content issues, and JD comparison issues

#### 22. No prioritized fix order
- Why it is important:
  - users need action order, not just a flat list
- What must be fixed:
  - sort output into:
    - fix first
    - improve next
    - optional

#### 23. Scoring formula is too shallow for launch trust
- Why it is important:
  - the system should not pretend to be accurate if it is using weak generic scoring
- What must be fixed:
  - separate ATS readability score from JD match score
  - explain both clearly
  - avoid one over-simplified final score being the only thing users see

---

## 2. Can Be Fixed After The App Is Running

These are useful improvements, but they are not strict launch blockers if the necessary fixes above are done properly.

### Phase 1: Resume Parsing

#### 1. Font inconsistency logic is incomplete
- Can wait because:
  - useful for polish, but not a top blocker if core parsing works

#### 2. Link extraction for all role-specific sites
- Can wait because:
  - LinkedIn/GitHub/portfolio are helpful, but not required for initial reliable ATS scoring

#### 3. Word-count logic improvement beyond basic usability checks
- Can wait because:
  - once crude unfair penalties are reduced, fine-tuning can happen later

#### 4. Per-entity extraction confidence
- Can wait because:
  - overall parser confidence matters more for launch than deep per-field confidence

#### 5. DOCX support
- Can wait because:
  - you can launch with PDF-only if communicated clearly

---

### Phase 2: Comparison Between Resume And JD

#### 6. Domain-aware comparison
- Can wait because:
  - general technical comparison can still launch first

#### 7. Role-aware comparison by job family
- Can wait because:
  - useful, but the app can still launch with better generic comparison if it is honest about it

#### 8. Confidence-aware missing-term logic
- Can wait because:
  - valuable after parser confidence is already surfaced

#### 9. Taxonomy expansion workflow and structured versioning
- Can wait because:
  - current taxonomy can support rollout if the important categories work

#### 10. Benchmark dataset and formal evaluation metrics
- Can wait because:
  - needed for long-term quality, but not necessary to get the first usable version live

---

### Phase 3: Result Analysis And Scoring

#### 11. Role-aware reporting
- Can wait because:
  - generic structured reporting is enough for initial rollout

#### 12. Reporting schema versioning and analytics
- Can wait because:
  - important for scale and maintenance, not for first rollout

#### 13. Advanced explanation polish
- Can wait because:
  - once you have structured findings with reasons and recommendations, deeper polish can follow

#### 14. Report-history comparison and old-vs-new scoring views
- Can wait because:
  - useful product feature, not a launch blocker

#### 15. Fully refined final-score calibration
- Can wait because:
  - you can launch if you clearly separate ATS readability and JD match, then calibrate later

---

## Launch Rule

If you want to roll out the app quickly without harming trust, the app should not launch until these three conditions are true:

1. Resume parsing is reliable enough to detect low-quality extraction
2. Resume vs JD comparison distinguishes critical requirements from optional ones
3. Results explain the score clearly enough that users know what to fix

If any one of those three is still weak, the product may look polished but still feel incorrect to real users.

---

## Suggested Rollout Order

### Must do first
1. parser confidence and scanned PDF detection
2. heading-based section detection
3. structured parsed resume object
4. JD segmentation
5. required vs preferred comparison
6. years/education/certification comparison
7. structured issue reporting
8. severity + prioritized fix list

### Can do immediately after rollout
1. role-aware scoring
2. domain-aware matching
3. richer taxonomy management
4. report versioning
5. analytics and calibration refinement
