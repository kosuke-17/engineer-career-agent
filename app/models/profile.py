"""Profile-related models for Learning Path Agent."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile model for API."""

    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User's name")
    email: Optional[str] = Field(default=None, description="User's email")
    years_of_experience: float = Field(
        default=0, ge=0, description="Years of programming experience"
    )
    current_role: Optional[str] = Field(default=None, description="Current job role")
    target_role: Optional[str] = Field(default=None, description="Target job role")
    goal: str = Field(default="", description="Learning goal")
    learning_hours_per_week: int = Field(
        default=10, ge=0, description="Available learning hours per week"
    )
    preferred_learning_style: str = Field(
        default="project_based", description="Preferred learning style"
    )
    preferred_languages: list[str] = Field(
        default_factory=list, description="Preferred programming languages"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CreateProfileRequest(BaseModel):
    """Request to create a new user profile."""

    name: str = Field(..., description="User's name")
    email: Optional[str] = Field(default=None, description="User's email")
    years_of_experience: float = Field(
        default=0, ge=0, description="Years of programming experience"
    )
    current_role: Optional[str] = Field(default=None, description="Current job role")
    target_role: Optional[str] = Field(default=None, description="Target job role")
    goal: str = Field(default="", description="Learning goal")
    learning_hours_per_week: int = Field(
        default=10, ge=0, description="Available learning hours per week"
    )
    preferred_learning_style: str = Field(
        default="project_based", description="Preferred learning style"
    )
    preferred_languages: list[str] = Field(
        default_factory=list, description="Preferred programming languages"
    )


class UpdateProfileRequest(BaseModel):
    """Request to update user profile."""

    name: Optional[str] = None
    email: Optional[str] = None
    years_of_experience: Optional[float] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    goal: Optional[str] = None
    learning_hours_per_week: Optional[int] = None
    preferred_learning_style: Optional[str] = None
    preferred_languages: Optional[list[str]] = None


class ProfileHistoryItem(BaseModel):
    """History item for profile assessment history."""

    date: datetime
    session_id: str
    overall_level: float
    recommended_domain: Optional[str] = None
    summary: Optional[str] = None


class ProfileHistoryResponse(BaseModel):
    """Response for profile history."""

    user_id: str
    assessments: list[ProfileHistoryItem] = Field(default_factory=list)
    completed_courses: list[dict] = Field(default_factory=list)
    skill_history: list[dict] = Field(default_factory=list)
