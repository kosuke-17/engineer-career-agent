"""Create profile use case."""

from app.application.dto import CreateProfileRequest, ProfileResponse
from app.domain.entities import Learner
from app.domain.repositories import LearnerRepository
from app.domain.value_objects import LearningStyle


class CreateProfileUseCase:
    """Use case for creating a new learner profile."""

    def __init__(self, learner_repository: LearnerRepository):
        self.learner_repository = learner_repository

    async def execute(self, request: CreateProfileRequest) -> ProfileResponse:
        """Execute the use case.

        Args:
            request: The create profile request.

        Returns:
            ProfileResponse with the created profile.

        Raises:
            ValueError: If a profile already exists for this user.
        """
        # Check if profile already exists
        if request.user_id:
            existing = await self.learner_repository.find_by_id(request.user_id)
            if existing:
                raise ValueError(f"Profile already exists for user: {request.user_id}")

        # Create new learner
        learner = Learner.create(user_id=request.user_id)

        # Convert learning style strings to enum values
        preferred_styles = []
        for style in request.preferred_styles:
            try:
                preferred_styles.append(LearningStyle(style))
            except ValueError:
                continue

        # Update profile with provided data
        learner.update_profile(
            experience_years=request.experience_years,
            current_role=request.current_role,
            target_role=request.target_role,
            preferred_styles=preferred_styles,
            weekly_hours=request.weekly_hours,
            interests=request.interests,
            constraints=request.constraints,
        )

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

