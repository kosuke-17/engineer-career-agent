"""Learner entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..value_objects import DomainAptitude, LearningStyle, SkillScore


@dataclass
class LearnerProfile:
    """Profile information for a learner."""

    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    preferred_styles: list[LearningStyle] = field(default_factory=list)
    weekly_hours: Optional[int] = None
    interests: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Check if profile has minimum required information."""
        return (
            self.experience_years is not None
            and self.target_role is not None
            and self.weekly_hours is not None
        )


@dataclass
class Learner:
    """Entity representing a learner."""

    id: str = field(default_factory=lambda: str(uuid4()))
    profile: LearnerProfile = field(default_factory=LearnerProfile)
    skill_scores: list[SkillScore] = field(default_factory=list)
    domain_aptitudes: list[DomainAptitude] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(cls, user_id: Optional[str] = None) -> "Learner":
        """Factory method to create a new learner."""
        return cls(id=user_id or str(uuid4()))

    def update_profile(self, **kwargs) -> None:
        """Update learner profile with provided fields."""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        self.updated_at = datetime.now()

    def add_skill_score(self, score: SkillScore) -> None:
        """Add or update a skill score."""
        # Remove existing score for the same skill
        self.skill_scores = [s for s in self.skill_scores if s.skill_name != score.skill_name]
        self.skill_scores.append(score)
        self.updated_at = datetime.now()

    def add_domain_aptitude(self, aptitude: DomainAptitude) -> None:
        """Add or update a domain aptitude."""
        # Remove existing aptitude for the same domain
        self.domain_aptitudes = [a for a in self.domain_aptitudes if a.domain != aptitude.domain]
        self.domain_aptitudes.append(aptitude)
        self.updated_at = datetime.now()

    def get_skill_score(self, skill_name: str) -> Optional[SkillScore]:
        """Get skill score by name."""
        for score in self.skill_scores:
            if score.skill_name == skill_name:
                return score
        return None

    def get_domain_aptitude(self, domain: str) -> Optional[DomainAptitude]:
        """Get domain aptitude by domain name."""
        for aptitude in self.domain_aptitudes:
            if aptitude.domain.value == domain:
                return aptitude
        return None

    def get_recommended_domains(self) -> list[DomainAptitude]:
        """Get domains that are recommended for this learner."""
        return [a for a in self.domain_aptitudes if a.is_recommended()]

    def get_weak_skills(self) -> list[SkillScore]:
        """Get skills that need improvement."""
        return [s for s in self.skill_scores if s.needs_improvement()]

    def get_strong_skills(self) -> list[SkillScore]:
        """Get skills that are proficient."""
        return [s for s in self.skill_scores if s.is_proficient()]
