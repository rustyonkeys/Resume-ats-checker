"""Offline English spelling suggestions for prose, never automatic corrections."""

from functools import lru_cache
import re

from .document_features import EMAIL, LINK, WORD, matching_text
from .scoring_schema import check


TECHNICAL_WORDS = frozenset("""
api apis aws azure backend frontend fullstack github gitlab hackerrank html css
javascript typescript python pytorch tensorflow numpy pandas scipy sklearn scikit
streamlit snowflake sql mysql postgresql mongodb nosql kubernetes docker devops
fastapi flask django react nodejs jupyter colab pdf pdfplumber pdf2image nlp nltk
tfidf regex dbms crud firebase linux macos windows leetcode
optimisation visualisation tokenisation normalisation vectorisation summarisation
optimizing visualizing tokenizing normalizing vectorizing summarizing
optimising visualising tokenising normalising vectorising summarising
tokenization vectorizer vectoriser wrangling dataset datasets
preprocess preprocesses preprocessed preprocessing
""".split())
TOKEN = re.compile(r"(?<![\w.+/-])[A-Za-z]+(?:'[A-Za-z]+)?(?![\w.+/-])")


@lru_cache(maxsize=1)
def _dictionary():
    from spellchecker import SpellChecker

    dictionary = SpellChecker(language="en", distance=1)
    dictionary.word_frequency.load_words(TECHNICAL_WORDS)
    return dictionary


def analyze_spelling(features, policy, language="en"):
    if language != "en":
        return check("spelling", 0, status="unavailable",
                     message="Spelling analysis currently supports English prose only.")
    try:
        dictionary = _dictionary()
    except (ImportError, OSError, ValueError) as exc:
        return check("spelling", 0, status="unavailable",
                     message="The local English spelling dictionary is unavailable.",
                     suggestion="Install the backend requirements and retry.",
                     evidence={"error": type(exc).__name__})

    allowed = {word.casefold() for word in policy.spelling_allowed_words}
    for section in features["sections"]:
        if section["type"] == "skills":
            allowed.update(word.casefold() for line in section["lines"] for word in WORD.findall(line["text"]))
    occurrences = {}
    for section in features["sections"]:
        if section["type"] not in {"experience", "projects", "summary"}:
            continue
        for line in section["lines"]:
            text = matching_text(line["text"])
            text = LINK.sub(" ", EMAIL.sub(" ", text)).replace("\u2019", "'")
            tokens = list(TOKEN.finditer(text))
            if len(tokens) < 6:
                continue
            for index, token in enumerate(tokens):
                word = token.group()
                if not 4 <= len(word) <= 32 or word.isupper():
                    continue
                if word != word.lower() and not (index == 0 and word.istitle()):
                    continue
                lower = word.casefold()
                if lower not in allowed:
                    occurrences.setdefault(lower, []).append(line["line"])

    if not occurrences:
        return check("spelling", 0, status="not_applicable",
                     message="No supported prose available for spelling review.", confidence="medium")
    unknown = sorted(dictionary.unknown(occurrences))
    candidates = []
    for word in unknown[:policy.spelling_max_candidates]:
        suggestions = dictionary.candidates(word) or set()
        suggestions = sorted(suggestions, key=lambda candidate: (-dictionary.word_frequency[candidate], candidate))
        candidates.append({"word": word, "suggestions": suggestions[:3],
                           "lines": sorted(set(occurrences[word])), "occurrences": len(occurrences[word])})
    return check("spelling", 0, status="warning" if unknown else "pass", confidence="low",
                 message="Possible misspellings or unfamiliar terms need review." if unknown else
                         "No dictionary-unknown words found in the checked prose.",
                 suggestion="Review suggestions; add valid names or domain terms to the spelling allowlist." if unknown else "",
                 evidence={"language": "en", "checked_unique_words": len(occurrences),
                           "unknown_count": len(unknown), "candidates": candidates,
                           "truncated": len(unknown) > policy.spelling_max_candidates,
                           "scope": "English prose in experience, projects, and summary; names and skill terms filtered"})
