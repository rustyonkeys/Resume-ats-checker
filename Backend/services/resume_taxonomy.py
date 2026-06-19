import re
from typing import Dict, List, Set


RAW_TAXONOMY: Dict[str, List[str]] = {
    "tech": [
        "artificial intelligence",
        "automation",
        "big data",
        "business intelligence",
        "computer vision",
        "data analysis",
        "data engineering",
        "data science",
        "deep learning",
        "devops",
        "distributed systems",
        "etl",
        "feature engineering",
        "generative ai",
        "machine learning",
        "microservices",
        "mlops",
        "natural language processing",
        "predictive modeling",
        "software development",
        "statistical modeling",
    ],
    "tools": [
        "airflow",
        "docker",
        "figma",
        "git",
        "github",
        "gitlab",
        "jira",
        "jupyter",
        "kubectl",
        "kubernetes",
        "linux",
        "microsoft excel",
        "notion",
        "postman",
        "power bi",
        "slack",
        "snowflake",
        "tableau",
        "terraform",
        "visual studio code",
    ],
    "soft_skills": [
        "adaptability",
        "analytical thinking",
        "collaboration",
        "communication",
        "critical thinking",
        "leadership",
        "mentoring",
        "ownership",
        "presentation",
        "problem solving",
        "project management",
        "stakeholder management",
        "strategic thinking",
        "teamwork",
        "time management",
    ],
    "roles": [
        "ai engineer",
        "analytics engineer",
        "backend developer",
        "business analyst",
        "data analyst",
        "data engineer",
        "data scientist",
        "devops engineer",
        "frontend developer",
        "full stack developer",
        "machine learning engineer",
        "product analyst",
        "product manager",
        "software engineer",
    ],
    "certifications": [
        "aws certified cloud practitioner",
        "aws certified solutions architect",
        "azure fundamentals",
        "azure data engineer associate",
        "certified kubernetes administrator",
        "google professional data engineer",
        "google professional machine learning engineer",
        "pmp",
        "scrum master",
        "tableau desktop specialist",
    ],
    "degrees": [
        "bachelor of arts",
        "bachelor of engineering",
        "bachelor of science",
        "bca",
        "btech",
        "master of business administration",
        "master of computer applications",
        "master of science",
        "mca",
        "mtech",
        "phd",
    ],
    "cloud_platforms": [
        "aws",
        "azure",
        "databricks",
        "gcp",
        "google cloud platform",
        "heroku",
        "redshift",
        "sagemaker",
        "snowflake",
    ],
    "programming_languages": [
        "bash",
        "c",
        "c plus plus",
        "c sharp",
        "go",
        "java",
        "javascript",
        "matlab",
        "python",
        "r",
        "ruby",
        "scala",
        "sql",
        "typescript",
    ],
    "databases": [
        "cassandra",
        "dynamodb",
        "mongodb",
        "mysql",
        "oracle",
        "postgresql",
        "redis",
        "sqlite",
        "sql server",
    ],
    "analytics_tools": [
        "google analytics",
        "looker",
        "matplotlib",
        "microsoft excel",
        "numpy",
        "pandas",
        "power bi",
        "sas",
        "scikit learn",
        "seaborn",
        "spreadsheets",
        "statistics",
        "tableau",
    ],
    "frameworks": [
        "angular",
        "django",
        "fastapi",
        "flask",
        "hugging face transformers",
        "keras",
        "langchain",
        "next js",
        "node js",
        "pytorch",
        "react",
        "spring boot",
        "streamlit",
        "tensorflow",
    ],
    "industry_terms": [
        "ab testing",
        "agile",
        "ci cd",
        "customer segmentation",
        "dashboarding",
        "data governance",
        "data pipeline",
        "experimentation",
        "forecasting",
        "kpi",
        "regression",
        "scrum",
        "time series",
        "user research",
    ],
}


SYNONYM_TO_CANONICAL: Dict[str, str] = {
    "ai": "artificial intelligence",
    "artificial-intelligence": "artificial intelligence",
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "genai": "generative ai",
    "llm": "generative ai",
    "llms": "generative ai",
    "bi": "business intelligence",
    "etl pipelines": "etl",
    "powerbi": "power bi",
    "power-bi": "power bi",
    "ms excel": "microsoft excel",
    "excel": "microsoft excel",
    "vscode": "visual studio code",
    "vs code": "visual studio code",
    "ga": "google analytics",
    "sklearn": "scikit learn",
    "scikit-learn": "scikit learn",
    "numpy library": "numpy",
    "pandas library": "pandas",
    "tf": "tensorflow",
    "torch": "pytorch",
    "huggingface": "hugging face transformers",
    "transformers": "hugging face transformers",
    "nextjs": "next js",
    "next": "next js",
    "node": "node js",
    "nodejs": "node js",
    "reactjs": "react",
    "react.js": "react",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "c++": "c plus plus",
    "cpp": "c plus plus",
    "c#": "c sharp",
    "dotnet": "c sharp",
    ".net": "c sharp",
    "postgres": "postgresql",
    "postgres db": "postgresql",
    "mssql": "sql server",
    "sqlserver": "sql server",
    "mongo": "mongodb",
    "aws cloud": "aws",
    "amazon web services": "aws",
    "microsoft azure": "azure",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "google cloud platform gcp": "google cloud platform",
    "k8s": "kubernetes",
    "kubernete": "kubernetes",
    "docker containers": "docker",
    "iac": "terraform",
    "air flow": "airflow",
    "jira software": "jira",
    "pm": "product manager",
    "ba": "business analyst",
    "sde": "software engineer",
    "swe": "software engineer",
    "mle": "machine learning engineer",
    "ml engineer": "machine learning engineer",
    "ds": "data scientist",
    "de": "data engineer",
    "da": "data analyst",
    "fullstack developer": "full stack developer",
    "frontend engineer": "frontend developer",
    "backend engineer": "backend developer",
    "b tech": "btech",
    "b.e": "bachelor of engineering",
    "be": "bachelor of engineering",
    "b.sc": "bachelor of science",
    "m.sc": "master of science",
    "mba degree": "master of business administration",
    "mca degree": "master of computer applications",
    "ph.d": "phd",
    "aws ccp": "aws certified cloud practitioner",
    "aws solutions architect": "aws certified solutions architect",
    "az 900": "azure fundamentals",
    "cka": "certified kubernetes administrator",
    "pmi pmp": "pmp",
    "csm": "scrum master",
    "a/b testing": "ab testing",
    "a b testing": "ab testing",
    "ci/cd": "ci cd",
    "kpis": "kpi",
    "forecasting models": "forecasting",
}


def _normalize_term(term: str) -> str:
    term = term.lower().strip()
    term = term.replace("&", " and ")
    term = re.sub(r"[^a-z0-9+#.\s/]", " ", term)
    term = term.replace("/", " ")
    term = re.sub(r"\s+", " ", term)
    return term.strip()


def build_taxonomy() -> Dict[str, List[str]]:
    return {
        category: sorted({_normalize_term(term) for term in terms})
        for category, terms in RAW_TAXONOMY.items()
    }


def build_synonym_index() -> Dict[str, str]:
    normalized_taxonomy = build_taxonomy()
    synonym_index: Dict[str, str] = {}

    for terms in normalized_taxonomy.values():
        for term in terms:
            synonym_index[term] = term

    for synonym, canonical in SYNONYM_TO_CANONICAL.items():
        synonym_index[_normalize_term(synonym)] = _normalize_term(canonical)

    return synonym_index


TAXONOMY = build_taxonomy()
SYNONYM_INDEX = build_synonym_index()
CANONICAL_TERMS: Set[str] = {
    canonical for canonical in SYNONYM_INDEX.values()
}


def normalize_text(text: str) -> str:
    return _normalize_term(text)


def canonicalize_term(term: str) -> str:
    normalized = _normalize_term(term)
    return SYNONYM_INDEX.get(normalized, normalized)


def extract_taxonomy_matches(text: str) -> Dict[str, List[str]]:
    normalized_text = f" {normalize_text(text)} "
    matches: Dict[str, List[str]] = {}

    for category, terms in TAXONOMY.items():
        found = []
        for term in terms:
            if f" {term} " in normalized_text:
                found.append(term)
        if found:
            matches[category] = sorted(set(found))

    return matches
