# Resume Format Scoring (V1)

Deterministic, local analysis. No LLM calls. English spelling uses the local
dictionary bundled with `pyspellchecker` (see backend requirements). Rules are
initial heuristics, not a validated prediction of any ATS vendor's behavior.

```text
validation_result + existing parser blocks + temporary PDF path
                           |
           +---------------+---------------+
           v                               v
  document_features.py             layout_analyzer.py
  sections/contact/lines            pages/fonts/tables/columns
           |                               |
           v                               v
  structure_scoring.py              layout/readability rules
  text_quality.py                          |
           +---------------+---------------+
                           v
               resume_format_scoring.py
                           |
           score + evidence + warnings + coverage
```

## Files

| File | Responsibility |
| --- | --- |
| `scoring_schema.py` | Rule version, configurable thresholds, result helpers |
| `document_features.py` | Deterministic English heading aliases and text features |
| `text_quality.py` | Extractable text, page coverage, encoding noise |
| `structure_scoring.py` | Sections, contact, bullets, word/page counts |
| `layout_analyzer.py` | PDF observations and layout/readability checks |
| `image_analysis.py` | Divider classification and image content review |
| `spelling_analysis.py` | Offline English prose spelling suggestions |
| `spacing_analysis.py` | Section and inferred paragraph gap comparisons |
| `ocr_analysis.py`, `ocr_worker.py` | Bounded, local OCR with per-page provenance |
| `reading_order.py` | Geometric reading-order checks and reconstruction |
| `resume_format_scoring.py` | Public entry point and result aggregation |
| `tests/test_format_scoring.py` | Regression tests using generated PDFs |

## Call From The Backend

```python
from services.scoring import score_resume_format

format_result = score_resume_format(
    validation_result=validation_result,
    parsed_resume=parsed_resume,  # Existing list returned by parse_resume()
    file_path=temp_file_path,    # Call before deleting the temporary PDF
)
```

Close/flush the temporary upload before validation and analysis.
PDF analysis is synchronous; run it in a bounded worker when connecting an async
route. PyMuPDF does not support concurrent use from multiple threads; use process
workers for parallel PDF jobs (see the official documentation below).

Text features use the extraction selected by the pipeline. Validation can recover
scan text and reconstruct supported reading orders before calling the parser. Existing
parser blocks provide block counts; they are not treated as verified sections.
`result["features"]` includes sections with source line numbers, contact candidates,
line statistics, and word counts, suitable for later JSON persistence. It contains
resume text and contact data; do not include it in ordinary application logs.
Pass text and file from the same validation operation. No database writes occur.

Version `format-v1.1` keeps colon-labelled skill subsections (e.g. `Languages:`)
inside an active skills section; standalone `Languages` headings remain separate.
Bullet matching ignores invisible format characters without altering stored lines.
`features.contact_info.links` merges HTTP(S) links from text and PDF annotations,
deduplicating normalized URLs while preserving paths, queries, and fragments.
This includes project/certificate URLs as well as profile URLs, not just contacts.
`layout.pages[].links` records URI annotations with their bounding boxes. Mailto,
file, and other non-web targets are excluded from the contact link list; URLs are
never opened. Annotation extraction failures are recorded in `layout.errors`,
with that page's `links` set to `null`; text links remain available.

Version `format-v1.2` adds image classification, spelling review, and PDF section
and paragraph spacing checks. The maximum remains 40. Spelling and spacing are
advisory (zero-weight) checks, not additional penalties.

## OCR And Reading Order

Version `format-v1.3` adds both checks. `file_validation()` now performs PDF
analysis before rejecting insufficient text, then returns it as `pdf_analysis`.
The scorer reuses that analysis when the rule version and policy match. Pass the
same file and validation result together; this cache is not for unrelated files.
When choosing a custom policy, pass it to both validation (`scoring_policy=`)
and scoring (`policy=`).

```text
PDF -> native text and geometry
           |
           +-> likely scanned/image text -> bounded local OCR subprocess
           |                                   |
           +---------------- recovered text ---+
           |
           v
    reading-order verification
           |
    reconstructed text -> content validation -> parser -> scoring
```

OCR uses PyMuPDF and local Tesseract language data, not a hosted service or LLM.
It runs for pages with no native text but visible content, or substantial images
with very little overlapping native text. Small images and decorative dividers
do not normally trigger OCR. Vector outlines without native text also trigger it.
Native text is retained during partial OCR. Default limits are 3 OCR pages per
document, 20 seconds per page, 180 DPI, and 12 million rendered pixels. Oversized
embedded images in partial OCR are skipped. Configure these using `ScoringPolicy`.

Tesseract English data is already installed on the development machine. On a new
machine, install Tesseract with `eng.traineddata`, or set `TESSDATA_PREFIX` to the
directory containing the language files. `ocr_language="eng"` is the default;
additional language packs must be installed before selecting `eng+hin`, for example.
No additional Python dependency is required for OCR. `ocr_enabled=False` disables
it explicitly. The rest of PDF analysis remains synchronous; deploy the pipeline
in bounded process workers for concurrent uploads.

Per-page OCR states are `not_needed`, `recovered`, `no_text`, and `unavailable`.
Timeouts, missing language files, and exhausted budgets are explicit results.
An entirely unreadable upload still fails validation with the extraction reason.
Recovered text is not guaranteed accurate: original font measurements and spacing
cannot be recovered from synthesized OCR fonts. These checks remain unavailable.

Reading-order verification supports clear left-to-right single-column layouts
and two columns separated by a detected gutter. Full-width rows separate bands;
within each band, left-column text precedes right-column text. Source order is
compared against this geometric order and backward jumps are reported. The chosen
text is available in `layout.extracted_text`; each page includes `reading_order`
evidence, including its `ordered_text`. Complex/overlapping layouts, rotated text,
and detected tables are not treated as verified. The model is heuristic and does
not prove the author's intended semantic order, especially in complex sidebars.

OCR and reading order have no standalone score deductions. When recovery or
ordering is uncertain, negative text-dependent deductions are withheld rather
than treating an extraction failure as missing skills, contacts, or bullets.
Unresolved OCR also makes page coverage unavailable. The resulting score can be
partial; do not display its provisional percentage as a final score.

## New Checks

| Check | Behavior |
| --- | --- |
| Divider images | Ignore warnings for visible images at most 2pt thick, at least 20pt long, and at least 20:1 in aspect ratio |
| Other images | Flag for manual review; report whether extracted text overlaps the image |
| Image pages without text | Attempt OCR; unresolved recognition makes coverage unavailable rather than deducting for assumed missing content |
| Spelling | Suggest corrections for unknown English prose words, including source line numbers |
| Section spacing | Compare gaps before headings and after headings separately, within each page |
| Paragraph spacing | Compare inferred paragraph or bullet-item gaps within the same section and page |

Image geometry cannot establish whether a picture contains important text. A
photo or logo therefore does not automatically lose points. Partial image-text
loss remains a review warning; OCR or source comparison is needed to confirm it.
Fully image-only files can now pass validation when OCR recovers sufficient text.

Spelling reviews prose in summary, projects, and experience only. It skips short
lines, URLs, emails, acronyms, most proper-name patterns, and skill vocabulary.
These filters reduce false positives but can miss real typos. Unknown words are
not necessarily misspellings. Suggestions use edit distance 1, capped at 50 unique
unknown words per resume; evidence reports truncation. No resume text is sent to
an external spelling service. Add known terms without changing the shared dictionary:

```python
from services.scoring import ScoringPolicy

policy = ScoringPolicy(spelling_allowed_words=("companyname", "productname"))
result = score_resume_format(validation_result, parsed_resume, temp_file_path, policy=policy)
```

Spacing requires at least 3 comparable gaps. A deviation must exceed both 4pt and
50% of the group's median gap to trigger review. Wrapped lines within a block are
not independent paragraphs. Detected columns, tables, or rotated text make spacing
unavailable; too few comparable gaps yield `not_applicable`. Paragraph boundaries
are inferred from PDF blocks and bullet markers, not verified semantic paragraphs.
Intentional differences may be flagged, which is why no points are deducted.

## Scored Checks

| Component | Marks | Deductions |
| --- | ---: | --- |
| Parse quality | 8 | No readable characters: 4; pages without text: up to 4 |
| Sections | 7 | Unrecognized/empty skills: 2; education: 2; projects OR experience: 3 |
| Contact | 5 | Neither an email nor a phone candidate recognized: 5 |
| Bullets | 5 | Achievement section without recognized bullets: 1; long groups are advisory |
| Length | 5 | Outside configured word range: 1; each page above limit: 1, capped at 3 |
| Layout risks | 4 | Table/column checks are advisory; no automatic presence penalty |
| Readability | 3 | Substantial small text: 2; excessive font families: 1 |
| Text noise | 3 | Replacement/control characters: 1, or 3 above noise threshold |

Defaults: 150-1200 words, at most 2 pages, body text below 9pt covering more
than 20% of characters, at most 3 significant font families. These are adjustable
product rules for conventional resumes, not universal hiring requirements.

Compared with the original plan: no required LinkedIn/GitHub or guessed name,
no penalty for top-of-page contact information, no image/table/column presence
penalty, and no second short-text or encoding penalty in parse quality.
Projects can satisfy the experience check. Font subset prefixes and common
bold/italic suffixes are normalized. Tables and columns still need manual review.

## Interpreting Results

```text
Readable text?
  no  -> status=unscorable, score=null
  yes -> All weighted checks available?
           no  -> status=partial, score=null
                  assessed_score / assessed_max_score
                  provisional_percentage + coverage_percentage
           yes -> status=complete, score=0..40, percentage=0..100
```

`complete` means all weighted checks ran, not that every possible format issue
was checked. `status_scope` states this explicitly. `not_implemented_checks` is
now empty for the planned checks. `unavailable_checks` identifies implemented
checks that could not run for this input, such as spacing without PDF geometry
or English spelling on an unsupported language. Spelling and spacing results are
in `breakdown.text_noise.checks` and `breakdown.readability.checks`, respectively.
OCR and reading-order findings are in `breakdown.parse_quality.checks`.
Each check has a stable `rule_id`, status, score, maximum, deduction,
confidence, evidence, and suggestion. Confidence labels are heuristic, not
calibrated probabilities. Only show the complete `percentage` as the final score;
keep provisional results visibly labelled and show coverage alongside them.

Unavailable checks never receive automatic full marks. A missing PDF, a table
detector failure, an unsupported language, or missing achievement sections can
make the result partial. DOCX supports text checks but visual layout is unavailable.
`language="en"` is the default; callers should supply the actual language. English
section aliases do not support arbitrary or combined headings. Missing recognition
does not establish missing content; feedback explicitly asks users to review it.

Margins and page ratios are observations only. Arbitrary heading recognition,
complex semantic reading-order models, and rendered DOCX layout remain future work.
Long wrapped bullets are advisory because plain
text cannot reliably distinguish continuation lines from subsequent job headings.

## Verify And Extend

Run from the repository root:

```powershell
.\Backend\.venv\Scripts\python.exe -m unittest discover -s Backend/services/scoring/tests -v
```

Before assigning production meaning to score thresholds, annotate a representative
resume set across career stages, templates, and languages. Measure false positives
for each rule, adjust `ScoringPolicy`, and bump `RULE_VERSION` when rules change.
The current tests check behavior and regressions; they do not establish real-world
scoring accuracy or capacity for millions of users.

PDF APIs follow [PyMuPDF's page documentation](https://pymupdf.readthedocs.io/en/latest/page.html).
For deployment, see [PyMuPDF's multiprocessing guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html).
