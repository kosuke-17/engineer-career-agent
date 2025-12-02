"""Get profile use case."""

from typing import Optional

from app.application.dto import ProfileResponse
from app.domain.entities import Learner
from app.domain.repositories import LearnerRepository


class GetProfileUseCase:
    """Use case for getting a learner profile."""

    def __init__(self, learner_repository: LearnerRepository):
        self.learner_repository = learner_repository

    async def execute(self, user_id: str) -> Optional[ProfileResponse]:
        """Execute the use case.

        Args:
            user_id: The user ID.

        Returns:
            ProfileResponse if found, None otherwise.
        """
        learner = await self.learner_repository.find_by_id(user_id)
        if not learner:
            return None

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

