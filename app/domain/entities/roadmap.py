"""Learning roadmap entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from ..value_objects import EngineeringDomain


@dataclass
class LearningResource:
    """A learning resource (book, course, tutorial, etc.)."""

    title: str
    type: str  # e.g., "course", "book", "tutorial", "project"
    url: Optional[str] = None
    estimated_hours: Optional[int] = None
    priority: int = 1  # 1=highest priority

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "type": self.type,
            "url": self.url,
            "estimated_hours": self.estimated_hours,
            "priority": self.priority,
        }


@dataclass
class Milestone:
    """A milestone in the learning journey."""

    title: str
    description: str
    skills: list[str] = field(default_factory=list)
    resources: list[LearningResource] = field(default_factory=list)
    estimated_weeks: int = 4
    is_completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "skills": self.skills,
            "resources": [r.to_dict() for r in self.resources],
            "estimated_weeks": self.estimated_weeks,
            "is_completed": self.is_completed,
        }


@dataclass
class QuarterPlan:
    """Plan for a quarter (3 months)."""

    quarter: int  # 1, 2, 3, or 4
    theme: str
    milestones: list[Milestone] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "quarter": self.quarter,
            "theme": self.theme,
            "milestones": [m.to_dict() for m in self.milestones],
            "goals": self.goals,
        }


@dataclass
class LearningRoadmap:
    """Entity representing a complete learning roadmap."""

    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    target_domain: Optional[EngineeringDomain] = None
    target_role: Optional[str] = None
    duration_months: int = 12
    quarters: list[QuarterPlan] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    final_project: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        user_id: str,
        target_domain: EngineeringDomain,
        target_role: str,
        duration_months: int = 12,
    ) -> "LearningRoadmap":
        """Factory method to create a new roadmap."""
        return cls(
            user_id=user_id,
            target_domain=target_domain,
            target_role=target_role,
            duration_months=duration_months,
        )

    def add_quarter(self, quarter_plan: QuarterPlan) -> None:
        """Add a quarter plan."""
        self.quarters.append(quarter_plan)
        self.updated_at = datetime.now()

    def get_current_quarter(self) -> Optional[QuarterPlan]:
        """Get the current quarter to work on."""
        for quarter in self.quarters:
            for milestone in quarter.milestones:
                if not milestone.is_completed:
                    return quarter
        return self.quarters[-1] if self.quarters else None

    def get_total_milestones(self) -> int:
        """Get total number of milestones."""
        return sum(len(q.milestones) for q in self.quarters)

    def get_completed_milestones(self) -> int:
        """Get number of completed milestones."""
        return sum(
            1
            for q in self.quarters
            for m in q.milestones
            if m.is_completed
        )

    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        total = self.get_total_milestones()
        completed = self.get_completed_milestones()
        return (completed / total) * 100 if total > 0 else 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_domain": self.target_domain.value if self.target_domain else None,
            "target_role": self.target_role,
            "duration_months": self.duration_months,
            "quarters": [q.to_dict() for q in self.quarters],
            "prerequisites": self.prerequisites,
            "final_project": self.final_project,
            "notes": self.notes,
            "progress_percentage": self.get_progress_percentage(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

