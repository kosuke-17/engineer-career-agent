"""Delete profile use case."""

from app.domain.repositories import LearnerRepository


class DeleteProfileUseCase:
    """Use case for deleting a learner profile."""

    def __init__(self, learner_repository: LearnerRepository):
        self.learner_repository = learner_repository

    async def execute(self, user_id: str) -> bool:
        """Execute the use case.

        Args:
            user_id: The user ID.

        Returns:
            True if the profile was deleted, False if not found.
        """
        return await self.learner_repository.delete(user_id)

