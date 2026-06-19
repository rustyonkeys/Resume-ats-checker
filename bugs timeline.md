# ApplyWise Bug Timeline

Goal: finish the most important backend bug work in 1-2 weeks.

This timeline assumes focused work on the backend parser, JD comparison, and reporting pipeline. It prioritizes fixes that unblock the rest of the product.

---

## Week 1

### Day 1: Resume Parsing Foundation
- Audit current parser flow in `Backend/resume.py`
- Add backend validation checklist for:
  - wrong file type
  - empty file
  - unreadable PDF
  - oversize file
- Define parser confidence fields
- Define parsing warning categories

Deliverables:
- parsing-state design
- validation plan
- error-state plan

### Day 2: Text Normalization and Bullet Fixes
- Fix unicode normalization strategy
- Standardize bullet detection behavior
- Clean extracted text more safely
- Add line-wise extraction preparation

Deliverables:
- normalized text pipeline
- bullet normalization strategy

### Day 3: Section Detection Rebuild
- Create canonical section map and aliases
- Replace exact-string section checks
- Detect heading-like lines and map them to sections
- Separate missing section vs unclear section

Deliverables:
- reliable section detection plan
- parsed section structure

### Day 4: Contact and Link Extraction
- Improve email and phone extraction
- Add LinkedIn extraction
- Add GitHub extraction
- Add portfolio/website extraction
- Define extraction confidence rules

Deliverables:
- contact entity parsing
- link extraction design

### Day 5: Layout and Extraction Risk Checks
- Rework multi-column detection logic
- Improve table/image risk logic
- Improve font-consistency logic
- Improve contact-placement risk logic
- Replace crude word-count-only logic

Deliverables:
- ATS layout risk rules
- formatting risk checklist

### Day 6: Structured Parsed Resume Object
- Create one internal parsed resume structure
- Move raw parsing outputs into structured fields
- Ensure downstream scoring reads from structured data, not only full text

Deliverables:
- parsed resume object design
- Phase 1 integration checkpoint

### Day 7: Phase 1 QA and Cleanup
- Test on multiple resume samples
- Test on good single-column resume
- Test on two-column resume
- Test on image-heavy resume
- Test on poor extraction PDF
- Fix regressions

Deliverables:
- Phase 1 stabilization
- bug list update

---

## Week 2

### Day 8: JD Segmentation
- Split JD into:
  - required skills
  - preferred skills
  - tools/platforms
  - education
  - certifications
  - responsibilities
- Remove JD noise blocks

Deliverables:
- structured JD parser plan

### Day 9: Weighted Matching Logic
- Replace flat keyword matching with category-based matching
- Weight required skills higher
- Add evidence-based match strength
- Add missing critical requirements list

Deliverables:
- Phase 2 scoring redesign

### Day 10: Experience, Education, Certification Comparison
- Add years-of-experience extraction from JD
- Define resume experience estimation approach
- Add education comparison logic
- Add certification comparison logic

Deliverables:
- requirement comparison design

### Day 11: Structured Result Schema
- Replace plain issue strings with structured issue objects
- Add categories:
  - parsing
  - format
  - content
  - JD match
- Add severity labels

Deliverables:
- report object schema

### Day 12: Score Explanation and Fix Prioritization
- Add explanation for each score component
- Add evidence per finding
- Add fix recommendation per finding
- Add priority grouping:
  - fix first
  - improve next
  - optional

Deliverables:
- Phase 3 explanation layer

### Day 13: Confidence-Aware Reporting
- Surface parser confidence in final report
- Reduce confidence of missing deductions when parsing is weak
- Add report messaging for:
  - no JD
  - weak parse quality
  - likely scanned PDF
  - incomplete evidence

Deliverables:
- safer result presentation

### Day 14: Final QA and Production Readiness Review
- Validate end-to-end flow
- Review false positives and false negatives
- Review report clarity
- Check response schema stability
- Prepare next backlog after these bugs

Deliverables:
- backend bug-fix milestone complete
- next-phase roadmap

---

## Priority Labels

### P0: Must finish in this 1-2 week window
- parser confidence
- normalization fix
- bullet fix
- section detection rebuild
- backend file validation
- JD segmentation
- weighted matching
- structured issue schema
- severity labels
- fix prioritization

### P1: Strongly recommended in same window if time allows
- link extraction
- experience comparison
- education comparison
- certification comparison
- smarter multi-column logic
- parser-confidence-aware reporting

### P2: Can move just after this window
- role-aware reporting
- domain-aware comparison
- telemetry/versioning
- broader benchmark dataset work

---

## Success Criteria For The 2-Week Window

By the end of this timeline, the backend should:

- reject bad files safely
- detect low-confidence parsing
- parse sections more reliably
- normalize bullets and noisy text correctly
- compare resumes and JDs by category instead of flat string counts
- explain issues with severity and fixes
- surface uncertainty instead of pretending all scores are equally trustworthy

---

## Notes

- Do not try to solve every future feature in this window.
- The goal is to remove the biggest trust-breaking bugs first.
- Phase 1 quality improvements should come before deep Phase 2 and Phase 3 polish.
