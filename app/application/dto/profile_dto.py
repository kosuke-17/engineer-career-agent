"""Profile DTOs."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CreateProfileRequest:
    """Request to create a new learner profile."""

    user_id: Optional[str] = None
    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    preferred_styles: list[str] = field(default_factory=list)
    weekly_hours: Optional[int] = None
    interests: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


@dataclass
class UpdateProfileRequest:
    """Request to update a learner profile."""

    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    preferred_styles: Optional[list[str]] = None
    weekly_hours: Optional[int] = None
    interests: Optional[list[str]] = None
    constraints: Optional[list[str]] = None


@dataclass
class ProfileResponse:
    """Response with learner profile."""

    user_id: str
    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    preferred_styles: list[str] = field(default_factory=list)
    weekly_hours: Optional[int] = None
    interests: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    skill_scores: list[dict[str, Any]] = field(default_factory=list)
    domain_aptitudes: list[dict[str, Any]] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

