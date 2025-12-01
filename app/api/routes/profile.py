"""Profile API endpoints."""

from typing import Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Depends

from app.config import get_settings, Settings
from app.storage.file_backend import FileBackend
from app.storage.schemas import LearnerProfile, LearningPreferences, LearningStyle
from app.models.profile import (
    UserProfile,
    CreateProfileRequest,
    UpdateProfileRequest,
    ProfileHistoryResponse,
    ProfileHistoryItem,
)

router = APIRouter()


def get_file_backend(settings: Settings = Depends(get_settings)) -> FileBackend:
    """Get file backend instance."""
    return FileBackend(
        memories_dir=settings.memories_dir,
        sessions_dir=settings.sessions_dir,
    )


@router.post("/", response_model=UserProfile)
async def create_profile(
    request: CreateProfileRequest,
    backend: FileBackend = Depends(get_file_backend),
) -> UserProfile:
    """
    Create a new user profile.

    Args:
        request: Profile creation request

    Returns:
        Created user profile
    """
    try:
        user_id = str(uuid.uuid4())

        # Create learner profile
        profile = LearnerProfile(
            user_id=user_id,
            name=request.name,
            years_of_experience=request.years_of_experience,
            goal=request.goal,
            learning_hours_per_week=request.learning_hours_per_week,
            preferred_learning_style=LearningStyle(request.preferred_learning_style),
            current_role=request.current_role,
            target_role=request.target_role,
        )

        # Save profile
        success = await backend.save_profile(profile)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save profile")

        # Create learning preferences
        preferences = LearningPreferences(
            user_id=user_id,
            project_based=request.preferred_learning_style == "project_based",
            preferred_languages=request.preferred_languages,
        )
        await backend.save_preferences(preferences)

        return UserProfile(
            user_id=user_id,
            name=request.name,
            email=request.email,
            years_of_experience=request.years_of_experience,
            current_role=request.current_role,
            target_role=request.target_role,
            goal=request.goal,
            learning_hours_per_week=request.learning_hours_per_week,
            preferred_learning_style=request.preferred_learning_style,
            preferred_languages=request.preferred_languages,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserProfile)
async def get_profile(
    user_id: str,
    backend: FileBackend = Depends(get_file_backend),
) -> UserProfile:
    """
    Get a user profile by ID.

    Args:
        user_id: User identifier

    Returns:
        User profile
    """
    try:
        profile = await backend.get_profile(user_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        preferences = await backend.get_preferences(user_id)

        return UserProfile(
            user_id=profile.user_id,
            name=profile.name,
            years_of_experience=profile.years_of_experience,
            current_role=profile.current_role,
            target_role=profile.target_role,
            goal=profile.goal,
            learning_hours_per_week=profile.learning_hours_per_week,
            preferred_learning_style=profile.preferred_learning_style.value,
            preferred_languages=preferences.preferred_languages if preferences else [],
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=UserProfile)
async def update_profile(
    user_id: str,
    request: UpdateProfileRequest,
    backend: FileBackend = Depends(get_file_backend),
) -> UserProfile:
    """
    Update a user profile.

    Args:
        user_id: User identifier
        request: Profile update request

    Returns:
        Updated user profile
    """
    try:
        # Get existing profile
        profile = await backend.get_profile(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Update fields
        if request.name is not None:
            profile.name = request.name
        if request.years_of_experience is not None:
            profile.years_of_experience = request.years_of_experience
        if request.current_role is not None:
            profile.current_role = request.current_role
        if request.target_role is not None:
            profile.target_role = request.target_role
        if request.goal is not None:
            profile.goal = request.goal
        if request.learning_hours_per_week is not None:
            profile.learning_hours_per_week = request.learning_hours_per_week
        if request.preferred_learning_style is not None:
            profile.preferred_learning_style = LearningStyle(request.preferred_learning_style)

        profile.updated_at = datetime.now()

        # Save updated profile
        success = await backend.save_profile(profile)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile")

        # Update preferences if needed
        if request.preferred_languages is not None:
            preferences = await backend.get_preferences(user_id)
            if preferences:
                preferences.preferred_languages = request.preferred_languages
                await backend.save_preferences(preferences)

        preferences = await backend.get_preferences(user_id)

        return UserProfile(
            user_id=profile.user_id,
            name=profile.name,
            years_of_experience=profile.years_of_experience,
            current_role=profile.current_role,
            target_role=profile.target_role,
            goal=profile.goal,
            learning_hours_per_week=profile.learning_hours_per_week,
            preferred_learning_style=profile.preferred_learning_style.value,
            preferred_languages=preferences.preferred_languages if preferences else [],
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_profile(
    user_id: str,
    backend: FileBackend = Depends(get_file_backend),
) -> dict:
    """
    Delete a user profile.

    Args:
        user_id: User identifier

    Returns:
        Deletion confirmation
    """
    try:
        profile = await backend.get_profile(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Delete profile file
        await backend.delete_file(f"/memories/{user_id}/profile.json")

        # Delete preferences file
        await backend.delete_file(f"/memories/{user_id}/learning_preferences.json")

        return {
            "success": True,
            "message": f"Profile {user_id} deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/history", response_model=ProfileHistoryResponse)
async def get_profile_history(
    user_id: str,
    backend: FileBackend = Depends(get_file_backend),
) -> ProfileHistoryResponse:
    """
    Get assessment history for a user.

    Args:
        user_id: User identifier

    Returns:
        Assessment history, completed courses, and skill history
    """
    try:
        # Check if user exists
        profile = await backend.get_profile(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Get assessment history
        assessment_history = await backend.get_assessment_history(user_id)
        assessments = [
            ProfileHistoryItem(
                date=datetime.fromisoformat(a.get("date", datetime.now().isoformat())),
                session_id=a.get("session_id", ""),
                overall_level=a.get("overall_level", 0),
                recommended_domain=a.get("recommended_domain"),
                summary=a.get("summary"),
            )
            for a in assessment_history
        ]

        # Get completed courses
        completed_courses = await backend.get_completed_courses(user_id)
        courses = [c.model_dump() for c in completed_courses]

        # Get skill history
        skill_history = await backend.get_skill_history(user_id)
        skills = [s.model_dump() for s in skill_history]

        return ProfileHistoryResponse(
            user_id=user_id,
            assessments=assessments,
            completed_courses=courses,
            skill_history=skills,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

