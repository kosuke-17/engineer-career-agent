"""Roadmap repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities import LearningRoadmap


class RoadmapRepository(ABC):
    """Abstract repository for LearningRoadmap entity."""

    @abstractmethod
    async def find_by_id(self, roadmap_id: str) -> Optional[LearningRoadmap]:
        """Find a roadmap by ID.

        Args:
            roadmap_id: The unique identifier of the roadmap.

        Returns:
            The LearningRoadmap entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> list[LearningRoadmap]:
        """Find all roadmaps for a user.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            List of LearningRoadmap entities.
        """
        pass

    @abstractmethod
    async def find_latest_by_user_id(self, user_id: str) -> Optional[LearningRoadmap]:
        """Find the latest roadmap for a user.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            The latest LearningRoadmap if found, None otherwise.
        """
        pass

    @abstractmethod
    async def save(self, roadmap: LearningRoadmap) -> None:
        """Save a roadmap.

        Args:
            roadmap: The LearningRoadmap entity to save.
        """
        pass

    @abstractmethod
    async def delete(self, roadmap_id: str) -> bool:
        """Delete a roadmap by ID.

        Args:
            roadmap_id: The unique identifier of the roadmap.

        Returns:
            True if the roadmap was deleted, False if not found.
        """
        pass
