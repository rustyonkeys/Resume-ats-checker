from typing import Callable, Dict, List, Optional, Tuple


class JobDescriptionMatchingService:
    """Match resume keywords against curated terms found in a job description."""

    def match(
        self,
        cleaned_resume_text: str,
        job_description: Optional[str] = None,
    ) -> Tuple[float, List[str], List[str], Dict[str, List[str]]]:
        if not job_description:
            return 0.0, [], [], {}

        taxonomy, canonicalize_term, normalize_text = self._load_taxonomy()
        resume_clean = f" {normalize_text(cleaned_resume_text)} "
        jd_clean = normalize_text(job_description)
        jd_terms_by_category = self._extract_taxonomy_terms_by_category(
            jd_clean,
            taxonomy,
        )

        matched = []
        missing = []
        matched_by_category: Dict[str, List[str]] = {}

        for category, terms in jd_terms_by_category.items():
            category_matches = []

            for term in terms:
                canonical_term = canonicalize_term(term)
                if f" {canonical_term} " in resume_clean:
                    category_matches.append(canonical_term)
                    matched.append(canonical_term)
                else:
                    missing.append(canonical_term)

            if category_matches:
                matched_by_category[category] = sorted(set(category_matches))

        matched = sorted(set(matched))
        missing = sorted(set(missing))

        total_jd_terms = sum(len(terms) for terms in jd_terms_by_category.values())
        keyword_score = (len(matched) / total_jd_terms) * 100 if total_jd_terms else 0

        return round(keyword_score, 2), matched, missing, matched_by_category

    def _extract_taxonomy_terms_by_category(
        self,
        cleaned_job_description: str,
        taxonomy: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        jd_terms_by_category: Dict[str, List[str]] = {}

        for category, terms in taxonomy.items():
            category_hits = [
                term for term in terms if f" {term} " in f" {cleaned_job_description} "
            ]

            if category_hits:
                jd_terms_by_category[category] = sorted(set(category_hits))

        return jd_terms_by_category

    def _load_taxonomy(
        self,
    ) -> Tuple[
        Dict[str, List[str]],
        Callable[[str], str],
        Callable[[str], str],
    ]:
        try:
            from services.resume_taxonomy import (
                TAXONOMY,
                canonicalize_term,
                normalize_text,
            )
        except ImportError:
            from Backend.services.resume_taxonomy import (
                TAXONOMY,
                canonicalize_term,
                normalize_text,
            )

        return TAXONOMY, canonicalize_term, normalize_text
