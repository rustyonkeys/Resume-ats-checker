from typing import Dict


class ResumeContentScoringService:
    """Score resume completeness from extracted resume features."""

    FEATURE_WEIGHTS = {
        "email": 10,
        "phone": 10,
        "has_experience": 10,
        "has_education": 5,
        "has_skills": 10,
        "has_projects": 5,
    }

    def calculate_score(self, features: Dict[str, bool]) -> int:
        total_score = 50
        missing_features = [feature for feature, exists in features.items() if not exists]

        for feature in missing_features:
            total_score -= self.FEATURE_WEIGHTS.get(feature, 0)

        return max(0, total_score)
