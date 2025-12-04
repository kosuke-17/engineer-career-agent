"""Skill score value object."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SkillLevel(str, Enum):
    """Skill level classification."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

    @classmethod
    def from_score(cls, score: float) -> "SkillLevel":
        """Determine skill level from score."""
        if score < 3:
            return cls.BEGINNER
        elif score < 6:
            return cls.INTERMEDIATE
        elif score < 8:
            return cls.ADVANCED
        else:
            return cls.EXPERT


@dataclass(frozen=True)
class SkillScore:
    """Value object representing a skill score."""

    skill_name: str
    score: float
    level: SkillLevel
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate score range."""
        if not 0 <= self.score <= 10:
            raise ValueError(f"Score must be between 0 and 10, got {self.score}")

    @classmethod
    def create(
        cls,
        skill_name: str,
        score: float,
        notes: Optional[str] = None,
    ) -> "SkillScore":
        """Create a skill score with auto-determined level."""
        level = SkillLevel.from_score(score)
        return cls(skill_name=skill_name, score=score, level=level, notes=notes)

    def is_proficient(self) -> bool:
        """Check if the skill level indicates proficiency."""
        return self.level in (SkillLevel.ADVANCED, SkillLevel.EXPERT)

    def needs_improvement(self) -> bool:
        """Check if the skill needs improvement."""
        return self.level in (SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE)
