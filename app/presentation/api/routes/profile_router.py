"""Profile API router."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.dto import (
    CreateProfileRequest,
    UpdateProfileRequest,
)
from app.application.use_cases import (
    CreateProfileUseCase,
    DeleteProfileUseCase,
    GetProfileUseCase,
    UpdateProfileUseCase,
)
from app.presentation.api.dependencies import (
    get_create_profile_use_case,
    get_delete_profile_use_case,
    get_get_profile_use_case,
    get_update_profile_use_case,
)

router = APIRouter()


# Request/Response models for API
class CreateProfileRequestModel(BaseModel):
    """Request to create a new profile."""

    user_id: Optional[str] = None
    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    preferred_styles: list[str] = []
    weekly_hours: Optional[int] = None
    interests: list[str] = []
    constraints: list[str] = []


class UpdateProfileRequestModel(BaseModel):
    """Request to update a profile."""

    experience_years: Optional[int] = None
    current_role: Optional[str] = None
    target_role: Optional[str] = None
    preferred_styles: Optional[list[str]] = None
    weekly_hours: Optional[int] = None
    interests: Optional[list[str]] = None
    constraints: Optional[list[str]] = None


class ProfileResponseModel(BaseModel):
    """Response with profile data."""

    user_id: str
    experience_years: Optional[int]
    current_role: Optional[str]
    target_role: Optional[str]
    preferred_styles: list[str]
    weekly_hours: Optional[int]
    interests: list[str]
    constraints: list[str]
    skill_scores: list[dict[str, Any]]
    domain_aptitudes: list[dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]


class DeleteResponseModel(BaseModel):
    """Response after deletion."""

    success: bool
    message: str


@router.post("/", response_model=ProfileResponseModel)
async def create_profile(
    request: CreateProfileRequestModel,
    use_case: CreateProfileUseCase = Depends(get_create_profile_use_case),
) -> ProfileResponseModel:
    """Create a new learner profile.

    Args:
        request: The create profile request.
        use_case: The create profile use case.

    Returns:
        ProfileResponseModel with the created profile.

    Raises:
        HTTPException: If the profile already exists.
    """
    try:
        dto_request = CreateProfileRequest(
            user_id=request.user_id,
            experience_years=request.experience_years,
            current_role=request.current_role,
            target_role=request.target_role,
            preferred_styles=request.preferred_styles,
            weekly_hours=request.weekly_hours,
            interests=request.interests,
            constraints=request.constraints,
        )
        result = await use_case.execute(dto_request)

        return ProfileResponseModel(
            user_id=result.user_id,
            experience_years=result.experience_years,
            current_role=result.current_role,
            target_role=result.target_role,
            preferred_styles=result.preferred_styles,
            weekly_hours=result.weekly_hours,
            interests=result.interests,
            constraints=result.constraints,
            skill_scores=result.skill_scores,
            domain_aptitudes=result.domain_aptitudes,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{user_id}", response_model=ProfileResponseModel)
async def get_profile(
    user_id: str,
    use_case: GetProfileUseCase = Depends(get_get_profile_use_case),
) -> ProfileResponseModel:
    """Get a learner profile.

    Args:
        user_id: The user ID.
        use_case: The get profile use case.

    Returns:
        ProfileResponseModel with the profile.

    Raises:
        HTTPException: If the profile is not found.
    """
    result = await use_case.execute(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")

    return ProfileResponseModel(
        user_id=result.user_id,
        experience_years=result.experience_years,
        current_role=result.current_role,
        target_role=result.target_role,
        preferred_styles=result.preferred_styles,
        weekly_hours=result.weekly_hours,
        interests=result.interests,
        constraints=result.constraints,
        skill_scores=result.skill_scores,
        domain_aptitudes=result.domain_aptitudes,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.put("/{user_id}", response_model=ProfileResponseModel)
async def update_profile(
    user_id: str,
    request: UpdateProfileRequestModel,
    use_case: UpdateProfileUseCase = Depends(get_update_profile_use_case),
) -> ProfileResponseModel:
    """Update a learner profile.

    Args:
        user_id: The user ID.
        request: The update profile request.
        use_case: The update profile use case.

    Returns:
        ProfileResponseModel with the updated profile.

    Raises:
        HTTPException: If the profile is not found.
    """
    try:
        dto_request = UpdateProfileRequest(
            experience_years=request.experience_years,
            current_role=request.current_role,
            target_role=request.target_role,
            preferred_styles=request.preferred_styles,
            weekly_hours=request.weekly_hours,
            interests=request.interests,
            constraints=request.constraints,
        )
        result = await use_case.execute(user_id, dto_request)

        return ProfileResponseModel(
            user_id=result.user_id,
            experience_years=result.experience_years,
            current_role=result.current_role,
            target_role=result.target_role,
            preferred_styles=result.preferred_styles,
            weekly_hours=result.weekly_hours,
            interests=result.interests,
            constraints=result.constraints,
            skill_scores=result.skill_scores,
            domain_aptitudes=result.domain_aptitudes,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{user_id}", response_model=DeleteResponseModel)
async def delete_profile(
    user_id: str,
    use_case: DeleteProfileUseCase = Depends(get_delete_profile_use_case),
) -> DeleteResponseModel:
    """Delete a learner profile.

    Args:
        user_id: The user ID.
        use_case: The delete profile use case.

    Returns:
        DeleteResponseModel with the result.
    """
    success = await use_case.execute(user_id)

    if success:
        return DeleteResponseModel(
            success=True,
            message=f"Profile {user_id} deleted successfully",
        )
    else:
        return DeleteResponseModel(
            success=False,
            message=f"Profile {user_id} not found",
        )
