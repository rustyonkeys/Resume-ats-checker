"""Extract scoring features without changing the existing block parser API."""

import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


SECTION_ALIASES = {
    "skills": {"skills", "technical skills", "key skills", "core skills",
               "technologies", "tech stack", "technical competencies"},
    "education": {"education", "academic background", "academics", "qualifications",
                  "qualification", "educational qualifications", "education and training"},
    "experience": {"experience", "work experience", "professional experience",
                   "employment history", "internship", "internships", "internship experience",
                   "relevant experience"},
    "projects": {"projects", "personal projects", "academic projects", "selected projects",
                 "major projects", "project experience", "technical projects"},
    "certifications": {"certifications", "certificates", "licenses", "courses"},
    "achievements": {"achievements", "awards", "honors", "accomplishments"},
    "summary": {"summary", "professional summary", "profile", "objective", "career objective"},
    "other": {"languages", "interests", "hobbies", "publications", "volunteering",
              "volunteer experience", "references", "leadership", "extracurricular activities"},
}
HEADINGS = {alias: section for section, aliases in SECTION_ALIASES.items() for alias in aliases}
SKILL_SUBSECTIONS = {
    "languages", "programming languages", "tools", "frameworks", "libraries",
    "databases", "technologies", "tech stack", "platforms", "technical competencies",
}
BULLET = re.compile(r"^\s*(?:[\u2022\u00b7\u25cf\u25aa\u25e6]\s*|[\u2013\u2014*+-]\s+|\d{1,2}[.)]\s+)\S")
EMAIL = re.compile(r"(?<![\w.+-])[\w.!#$%&'*+/=?^`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}(?![\w.-])")
PHONE = re.compile(r"(?<![\w])\+?\d[\d ()\-.]{5,}\d(?![\w])")
LINK = re.compile(r"(?:https?://|www\.)[^\s<>]+|(?:linkedin\.com/in/|github\.com/)[^\s<>]+", re.I)
WORD = re.compile(r"[^\W_]+(?:[+#.'-][^\W_]+)*", re.UNICODE)


def matching_text(value):
    """Ignore invisible format characters for matching, preserving source text."""
    return "".join(char for char in value if unicodedata.category(char) != "Cf")


def is_bullet_line(value):
    return bool(BULLET.match(matching_text(value)))


def normalize_web_link(value):
    """Canonicalize web URLs without changing case-sensitive paths or queries."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.lower().startswith(("www.", "linkedin.com/", "github.com/")):
        value = "https://" + value
    if any(char.isspace() or unicodedata.category(char) in {"Cc", "Cf"} for char in value):
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
            return None
        port = parts.port
        host = parts.hostname.lower()
        if ":" in host:
            host = f"[{host}]"
        if port is not None and (parts.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
            host += f":{port}"
        return urlunsplit((parts.scheme.lower(), host, parts.path or "/", parts.query, parts.fragment))
    except ValueError:
        return None


def normalize_heading(value):
    value = matching_text(value)
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    value = re.sub(r"^\d{1,2}[.)]\s+", "", value)
    return " ".join(value.strip(" :|.-").replace("&", " and ").split())


def detect_heading(line):
    """Accept whole headings or explicit 'Skills: Python', never substrings."""
    parts = line.split(":", 1)
    section = HEADINGS.get(normalize_heading(parts[0]))
    return (section, parts[1].strip() if len(parts) == 2 else "")


def extract_features(text, parsed_blocks=None, embedded_links=None):
    lines = [{"line": index, "text": value.strip()}
             for index, value in enumerate(text.splitlines(), 1) if value.strip()]
    sections = []
    current = None
    for line in lines:
        label, separator, content = line["text"].partition(":")
        if (current is not None and current["type"] == "skills" and separator
                and normalize_heading(label) in SKILL_SUBSECTIONS):
            current["lines"].append({**line, "is_subheading": not bool(matching_text(content).strip())})
            continue
        section_type, inline_content = detect_heading(line["text"])
        if section_type:
            current = {"type": section_type, "heading": line["text"].split(":", 1)[0],
                       "line": line["line"], "lines": []}
            sections.append(current)
            if inline_content:
                current["lines"].append({"line": line["line"], "text": inline_content})
        elif current is not None:
            current["lines"].append(line)

    phones = []
    for match in PHONE.finditer(text):
        candidate = match.group().strip()
        digits = re.sub(r"\D", "", candidate)
        # Exclude typical dates and year ranges before accepting a phone candidate.
        if not 10 <= len(digits) <= 15:
            continue
        if re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", candidate):
            continue
        if len(set(digits)) == 1:
            continue
        phones.append(candidate)

    bullet_lines = [line for line in lines if is_bullet_line(line["text"])]
    link_candidates = [value.rstrip(".,;)") for value in LINK.findall(text)]
    link_candidates.extend(embedded_links or [])
    links = {url for value in link_candidates if (url := normalize_web_link(value))}
    return {
        "sections": sections,
        "contact_info": {
            "emails": sorted(set(EMAIL.findall(text))),
            "phones": sorted(set(phones)),
            "links": sorted(links),
        },
        "lines": lines,
        "line_analysis": {"total_lines": len(lines), "bullet_lines": len(bullet_lines),
                          "bullet_ratio": round(len(bullet_lines) / max(1, len(lines)), 3)},
        "text_metrics": {"word_count": len(WORD.findall(text)), "character_count": len(text),
                         "alphanumeric_count": sum(char.isalnum() for char in text),
                         "block_count": len(parsed_blocks or [])},
    }
