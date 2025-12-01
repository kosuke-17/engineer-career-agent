"""Data schemas for Learning Path Agent storage."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LearningStyle(str, Enum):
    """Learning style preferences."""

    PROJECT_BASED = "project_based"
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    COMMUNITY = "community"


class SkillLevel(str, Enum):
    """Skill level enum."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class EngineeringDomain(str, Enum):
    """Engineering domain enum."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    DEVOPS = "devops"
    ML_ENGINEERING = "ml_engineering"
    SYSTEMS = "systems"
    MOBILE = "mobile"


class LearnerProfile(BaseModel):
    """Learner profile schema."""

    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="Learner's name")
    years_of_experience: float = Field(
        default=0, ge=0, description="Years of programming experience"
    )
    goal: str = Field(default="", description="Learning goal")
    learning_hours_per_week: int = Field(
        default=10, ge=0, description="Available learning hours per week"
    )
    preferred_learning_style: LearningStyle = Field(
        default=LearningStyle.PROJECT_BASED, description="Preferred learning style"
    )
    current_role: Optional[str] = Field(default=None, description="Current job role")
    target_role: Optional[str] = Field(default=None, description="Target job role")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SkillScore(BaseModel):
    """Individual skill score."""

    skill_name: str = Field(..., description="Name of the skill")
    score: float = Field(..., ge=0, le=10, description="Skill score (0-10)")
    level: SkillLevel = Field(default=SkillLevel.BEGINNER)
    notes: Optional[str] = Field(default=None, description="Additional notes")


class SkillHistory(BaseModel):
    """Skill history entry."""

    date: datetime = Field(default_factory=datetime.now)
    overall_level: float = Field(..., ge=0, le=10, description="Overall skill level")
    skills: list[SkillScore] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None)


class CompletedCourse(BaseModel):
    """Completed course record."""

    course_id: str = Field(..., description="Course identifier")
    course_name: str = Field(..., description="Course name")
    provider: Optional[str] = Field(default=None, description="Course provider")
    completed_at: datetime = Field(default_factory=datetime.now)
    score: Optional[float] = Field(default=None, ge=0, le=100, description="Completion score")
    duration_hours: Optional[float] = Field(default=None, description="Course duration")
    skills_gained: list[str] = Field(default_factory=list)


class DomainAptitude(BaseModel):
    """Domain aptitude score."""

    domain: EngineeringDomain
    score: float = Field(..., ge=0, le=10)
    reasoning: Optional[str] = Field(default=None)


class LearningPreferences(BaseModel):
    """Learning preferences schema."""

    user_id: str = Field(..., description="User identifier")
    difficulty_level: str = Field(default="gradual", description="Preferred difficulty progression")
    project_based: bool = Field(default=True)
    community_learning: bool = Field(default=False)
    preferred_languages: list[str] = Field(default_factory=list)
    preferred_domains: list[EngineeringDomain] = Field(default_factory=list)
    time_commitment: str = Field(default="moderate", description="Time commitment level")


class PhaseResult(BaseModel):
    """Result of a single diagnosis phase."""

    phase_number: int = Field(..., ge=1, le=5)
    phase_name: str
    status: str = Field(default="pending")  # pending, in_progress, completed
    skills_assessed: list[SkillScore] = Field(default_factory=list)
    domain_aptitudes: list[DomainAptitude] = Field(default_factory=list)
    notes: str = Field(default="")
    completed_at: Optional[datetime] = Field(default=None)


class AssessmentResult(BaseModel):
    """Complete assessment result."""

    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)
    phases: list[PhaseResult] = Field(default_factory=list)
    foundation_score: Optional[float] = Field(default=None, ge=0, le=10)
    recommended_domain: Optional[EngineeringDomain] = Field(default=None)
    roadmap: Optional[dict] = Field(default=None, description="Generated learning roadmap")
    overall_assessment: Optional[str] = Field(default=None)


class QuarterPlan(BaseModel):
    """Quarterly learning plan."""

    quarter: int = Field(..., ge=1, le=4)
    focus_areas: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    project: Optional[str] = Field(default=None)
    expected_hours: int = Field(default=0)
    milestones: list[str] = Field(default_factory=list)


class LearningRoadmap(BaseModel):
    """Complete learning roadmap."""

    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    recommended_domain: EngineeringDomain
    foundation_score: float
    learning_style: LearningStyle
    total_duration_months: int = Field(default=12)
    weekly_hours: int
    quarterly_plans: list[QuarterPlan] = Field(default_factory=list)
    resources: list[dict] = Field(default_factory=list)
    summary: str = Field(default="")
