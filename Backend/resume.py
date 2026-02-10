# resume.py
"""
ATS Resume Scorer - ML Model
Analyzes resumes for ATS compatibility
"""

import pdfplumber
import fitz  # PyMuPDF
import re
from typing import Dict, List, Tuple, Optional


class ResumeATSScorer:
    """
    Resume ATS Compatibility Scorer
    
    Usage:
        scorer = ResumeATSScorer(pdf_path)
        scorer.extract_text()
        scorer.clean_text(scorer.resume_text)
        scorer.extract_features()
        scorer.calculate_content_score()
        format_issues, format_score = scorer.check_format_issues()
        final_score = scorer.calculate_final_score()
    """
    
    def __init__(self, pdf_path: str):
        """
        Initialize scorer with PDF path
        
        Args:
            pdf_path: Path to resume PDF file
        """
        self.pdf_path = pdf_path
        self.resume_text = ""
        self.cleaned_text = ""
        self.features = {}
        self.content_score = 0
        self.format_score = 0
        self.keyword_score = 0
        self.total_score = 0
    
    def extract_text(self) -> str:
        """
        Extract text from PDF
        FROM YOUR CELL 5
        """
        text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        self.resume_text = text
        return text
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        FROM YOUR CELL 6
        """
        text = re.sub(r"\s+", " ", text)
        self.cleaned_text = text.strip().lower()
        return self.cleaned_text
    
    def extract_features(self) -> Dict[str, bool]:
        """
        Extract resume features (email, phone, sections)
        COMBINE CELLS 8, 9, 11, 12
        """
        text = self.cleaned_text
        
        # Email detection (Cell 8)
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, text)
        
        # Phone detection (Cell 9)
        phone_pattern = r"\+?[\d\s\-\(\)]{10,}"
        phones = re.findall(phone_pattern, text)
        
        # Section checking (Cell 11)
        sections = ["education", "skills", "experience", "projects", 
                   "certifications", "extracurricular activities"]
        found_sections = [s for s in sections if s in text]
        
        # Features dict (Cell 12)
        self.features = {
            "email": len(emails) > 0,
            "phone": len(phones) > 0,
            "has_experience": "experience" in text,
            "has_education": "education" in text,
            "has_skills": "skills" in text,
            "has_projects": "projects" in text,
            "has_certifications": "certifications" in text,
            "has_extracurricular_activities": "extracurricular activities" in text,
            "has_summary": any(word in text for word in ["summary", "objective", "profile"]),
            "has_achievements": any(word in text for word in ["achieved", "improved", "increased", "reduced"]),
            "has_metrics": bool(re.search(r'\d+%|\$\d+|[\d,]+\+', text))
        }
        
        return self.features
    
    def calculate_content_score(self) -> int:
        """
        Calculate content completeness score
        FROM YOUR CELL 18
        """
        feature_weights = {
            "email": 10,
            "phone": 10,
            "has_experience": 10,
            "has_education": 5,
            "has_skills": 10,
            "has_projects": 5,
        }
        
        # Start with base score
        total_score = 50
        
        # Get missing features (Cell 17)
        missing_features = [k for k, v in self.features.items() if not v]
        
        # Subtract weights for missing features
        for feature in missing_features:
            total_score -= feature_weights.get(feature, 0)
        
        self.content_score = max(0, total_score)  # Don't go below 0
        return self.content_score
    
    def check_format_issues(self) -> Tuple[List[str], int]:
        """
        Check formatting issues using PyMuPDF
        COMBINE CELLS 20, 21, 22, 23, 24, 25
        """
        issues = []
        score = 100
        
        doc = fitz.open(self.pdf_path)
        
        # Font check (Cell 22)
        font_sizes = {}
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            font = span["font"]
                            size = span["size"]
                            if font not in font_sizes:
                                font_sizes[font] = set()
                            font_sizes[font].add(size)
        
        inconsistent_fonts = {font: sizes for font, sizes in font_sizes.items() if len(sizes) > 1}
        if len(font_sizes) > 3:
            issues.append("Too many fonts used (recommend 1-2)")
            score -= 10
        
        # Contact info placement (Cell 23)
        for page in doc:
            blocks = page.get_text("blocks")
            height = page.rect.height
            for b in blocks:
                text = b[4]
                y0 = b[1]
                if re.search(r'\S+@\S+|\d{10}', text):
                    if y0 < 0.1 * height:
                        issues.append("Contact info in header (may be skipped by ATS)")
                        score -= 5
                    elif y0 > 0.9 * height:
                        issues.append("Contact info in footer (may be skipped by ATS)")
                        score -= 5
        
        # Tables and images (Cell 24)
        for page in doc:
            if page.get_images():
                issues.append("Contains images (ATS may not read content)")
                score -= 15
                break
        
        for page in doc:
            tables = page.find_tables()
            if tables.tables:
                issues.append("Contains tables (ATS may skip structured data)")
                score -= 10
                break
        
        # Multi-column check (Cell 25)
        for page in doc:
            blocks = page.get_text("blocks")
            if blocks:
                x_positions = [b[0] for b in blocks]
                if max(x_positions) - min(x_positions) > 300:
                    issues.append("Multi-column layout detected (ATS may misread order)")
                    score -= 15
                    break
        
        # Bullet points check
        if not any(char in self.resume_text for char in ['•', '-', '*', '·']):
            issues.append("No bullet points found")
            score -= 10
        
        # Required sections
        required_sections = ["experience", "education", "skills"]
        missing_sections = [s for s in required_sections if s not in self.cleaned_text]
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
            score -= 5 * len(missing_sections)
        
        # Length check
        word_count = len(self.cleaned_text.split())
        if word_count < 200:
            issues.append("Resume too short (< 200 words)")
            score -= 20
        elif word_count > 1000:
            issues.append("Resume too long (> 1000 words)")
            score -= 10
        
        self.format_score = max(0, score)
        return issues, self.format_score
    
    def match_job_description(self, job_description: Optional[str] = None) -> Tuple[float, List[str]]:
        """
        Match resume with job description
        TODO: Implement keyword matching and TF-IDF similarity
        """
        if not job_description:
            return 0.0, []
        
        # Basic keyword matching
        jd_clean = re.sub(r"\s+", " ", job_description.lower().strip())
        
        # Extract common tech keywords
        tech_keywords = re.findall(
            r'\b(?:python|sql|power bi|azure|aws|machine learning|'
            r'data analysis|excel|r|git|spark|hadoop|tableau)\b',
            jd_clean
        )
        
        # Count matches in resume
        matches = []
        for keyword in set(tech_keywords):
            if keyword in self.cleaned_text:
                matches.append(keyword)
        
        # Simple scoring
        if tech_keywords:
            self.keyword_score = (len(matches) / len(set(tech_keywords))) * 100
        else:
            self.keyword_score = 0
        
        return self.keyword_score, matches
    
    def calculate_final_score(self) -> float:
        """
        Calculate weighted final score
        Content: 40%, Format: 30%, Keywords: 30%
        """
        self.total_score = (
            self.content_score * 0.4 +
            self.format_score * 0.3 +
            self.keyword_score * 0.3
        )
        return round(self.total_score, 2)
    
    def get_missing_features(self) -> List[str]:
        """Get list of missing features in readable format"""
        return [
            k.replace('has_', '').replace('_', ' ').title()
            for k, v in self.features.items() if not v
        ]


# Optional: For testing the module directly
if __name__ == "__main__":
    # This only runs when you do: python resume.py
    # Won't run when imported in FastAPI
    
    import sys
    
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
        print(f"Testing with: {test_pdf}")
        
        scorer = ResumeATSScorer(test_pdf)
        scorer.extract_text()
        scorer.clean_text(scorer.resume_text)
        scorer.extract_features()
        scorer.calculate_content_score()
        issues, fmt_score = scorer.check_format_issues()
        
        print(f"Content Score: {scorer.content_score}")
        print(f"Format Score: {scorer.format_score}")
        print(f"Features: {scorer.features}")
        print(f"Issues: {issues}")
    else:
        print("Usage: python resume.py <path_to_pdf>")