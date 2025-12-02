"""Learner repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities import Learner


class LearnerRepository(ABC):
    """Abstract repository for Learner entity."""

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[Learner]:
        """Find a learner by their ID.

        Args:
            user_id: The unique identifier of the learner.

        Returns:
            The Learner entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def save(self, learner: Learner) -> None:
        """Save a learner entity.

        Args:
            learner: The Learner entity to save.
        """
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a learner by their ID.

        Args:
            user_id: The unique identifier of the learner.

        Returns:
            True if the learner was deleted, False if not found.
        """
        pass

    @abstractmethod
    async def exists(self, user_id: str) -> bool:
        """Check if a learner exists.

        Args:
            user_id: The unique identifier of the learner.

        Returns:
            True if the learner exists, False otherwise.
        """
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Learner]:
        """List all learners with pagination.

        Args:
            limit: Maximum number of learners to return.
            offset: Number of learners to skip.

        Returns:
            List of Learner entities.
        """
        pass

