"""Update profile use case."""

from app.application.dto import UpdateProfileRequest, ProfileResponse
from app.domain.entities import Learner
from app.domain.repositories import LearnerRepository
from app.domain.value_objects import LearningStyle


class UpdateProfileUseCase:
    """Use case for updating a learner profile."""

    def __init__(self, learner_repository: LearnerRepository):
        self.learner_repository = learner_repository

    async def execute(
        self, user_id: str, request: UpdateProfileRequest
    ) -> ProfileResponse:
        """Execute the use case.

        Args:
            user_id: The user ID.
            request: The update profile request.

        Returns:
            ProfileResponse with the updated profile.

        Raises:
            ValueError: If the profile is not found.
        """
        learner = await self.learner_repository.find_by_id(user_id)
        if not learner:
            raise ValueError(f"Profile not found: {user_id}")

        # Build update dictionary with only provided fields
        update_data = {}

        if request.experience_years is not None:
            update_data["experience_years"] = request.experience_years

        if request.current_role is not None:
            update_data["current_role"] = request.current_role

        if request.target_role is not None:
            update_data["target_role"] = request.target_role

        if request.preferred_styles is not None:
            preferred_styles = []
            for style in request.preferred_styles:
                try:
                    preferred_styles.append(LearningStyle(style))
                except ValueError:
                    continue
            update_data["preferred_styles"] = preferred_styles

        if request.weekly_hours is not None:
            update_data["weekly_hours"] = request.weekly_hours

        if request.interests is not None:
            update_data["interests"] = request.interests

        if request.constraints is not None:
            update_data["constraints"] = request.constraints

        # Update the profile
        learner.update_profile(**update_data)

        # Save the learner
        await self.learner_repository.save(learner)

        return self._to_response(learner)

    def _to_response(self, learner: Learner) -> ProfileResponse:
        """Convert learner entity to response."""
        return ProfileResponse(
            user_id=learner.id,
            experience_years=learner.profile.experience_years,
            current_role=learner.profile.current_role,
            target_role=learner.profile.target_role,
            preferred_styles=[s.value for s in learner.profile.preferred_styles],
            weekly_hours=learner.profile.weekly_hours,
            interests=learner.profile.interests,
            constraints=learner.profile.constraints,
            skill_scores=[
                {
                    "name": s.skill_name,
                    "score": s.score,
                    "level": s.level.value,
                    "notes": s.notes,
                }
                for s in learner.skill_scores
            ],
            domain_aptitudes=[
                {
                    "domain": a.domain.value,
                    "score": a.score,
                    "reasoning": a.reasoning,
                }
                for a in learner.domain_aptitudes
            ],
            created_at=learner.created_at.isoformat(),
            updated_at=learner.updated_at.isoformat(),
        )

