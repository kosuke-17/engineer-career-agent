"""Skill assessment domain service."""

from typing import Any

from ..entities import Learner
from ..value_objects import DomainAptitude, EngineeringDomain, SkillScore


class SkillAssessmentService:
    """Domain service for skill assessment operations."""

    @staticmethod
    def calculate_overall_score(learner: Learner) -> float:
        """Calculate overall skill score for a learner.

        Args:
            learner: The learner entity.

        Returns:
            Average score across all skills (0-10).
        """
        if not learner.skill_scores:
            return 0.0

        total = sum(score.score for score in learner.skill_scores)
        return total / len(learner.skill_scores)

    @staticmethod
    def get_skill_gaps(
        learner: Learner, required_skills: dict[str, float]
    ) -> list[tuple[str, float]]:
        """Identify skill gaps compared to required skills.

        Args:
            learner: The learner entity.
            required_skills: Dictionary of skill name to required score.

        Returns:
            List of (skill_name, gap) tuples where gap is positive if improvement needed.
        """
        gaps = []
        for skill_name, required_score in required_skills.items():
            current_score = learner.get_skill_score(skill_name)
            current = current_score.score if current_score else 0.0
            gap = required_score - current
            if gap > 0:
                gaps.append((skill_name, gap))

        # Sort by largest gap first
        gaps.sort(key=lambda x: x[1], reverse=True)
        return gaps

    @staticmethod
    def recommend_domains(learner: Learner) -> list[DomainAptitude]:
        """Recommend engineering domains based on skill scores.

        This is a rule-based recommendation that maps skills to domains.
        For AI-based recommendations, use the application layer.

        Args:
            learner: The learner entity.

        Returns:
            List of DomainAptitude objects sorted by recommendation score.
        """
        # Skill to domain mapping weights
        domain_skills = {
            EngineeringDomain.FRONTEND: [
                "javascript", "typescript", "css", "html", "react", "vue"
            ],
            EngineeringDomain.BACKEND: [
                "python", "java", "database", "api_design", "sql"
            ],
            EngineeringDomain.DEVOPS: [
                "linux", "docker", "kubernetes", "ci_cd", "cloud"
            ],
            EngineeringDomain.ML_ENGINEERING: [
                "python", "machine_learning", "statistics", "data_processing"
            ],
            EngineeringDomain.MOBILE: [
                "swift", "kotlin", "react_native", "flutter"
            ],
            EngineeringDomain.SYSTEMS: [
                "c", "rust", "operating_systems", "networking"
            ],
        }

        aptitudes = []
        for domain, skills in domain_skills.items():
            scores = []
            for skill_name in skills:
                skill_score = learner.get_skill_score(skill_name)
                if skill_score:
                    scores.append(skill_score.score)

            if scores:
                avg_score = sum(scores) / len(scores)
            else:
                avg_score = 0.0

            aptitudes.append(
                DomainAptitude(domain=domain, score=avg_score)
            )

        # Sort by score descending
        aptitudes.sort(key=lambda x: x.score, reverse=True)
        return aptitudes

    @staticmethod
    def parse_assessment_result(
        result: dict[str, Any]
    ) -> list[SkillScore]:
        """Parse assessment result from LLM into skill scores.

        Args:
            result: Dictionary containing skill assessment results.

        Returns:
            List of SkillScore value objects.
        """
        skill_scores = []

        skills_data = result.get("skills", [])
        if isinstance(skills_data, dict):
            skills_data = [
                {"name": k, "score": v.get("score", 0), "notes": v.get("notes")}
                for k, v in skills_data.items()
            ]

        for skill in skills_data:
            if isinstance(skill, dict) and "name" in skill and "score" in skill:
                try:
                    score = SkillScore.create(
                        skill_name=skill["name"],
                        score=float(skill["score"]),
                        notes=skill.get("notes"),
                    )
                    skill_scores.append(score)
                except (ValueError, TypeError):
                    continue

        return skill_scores

