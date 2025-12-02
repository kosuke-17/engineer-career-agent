"""Diagnosis repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities import DiagnosisSession


class DiagnosisRepository(ABC):
    """Abstract repository for DiagnosisSession entity."""

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[DiagnosisSession]:
        """Find a diagnosis session by ID.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            The DiagnosisSession entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> list[DiagnosisSession]:
        """Find all diagnosis sessions for a user.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            List of DiagnosisSession entities.
        """
        pass

    @abstractmethod
    async def find_active_by_user_id(
        self, user_id: str
    ) -> Optional[DiagnosisSession]:
        """Find the active (incomplete) diagnosis session for a user.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            The active DiagnosisSession if found, None otherwise.
        """
        pass

    @abstractmethod
    async def save(self, session: DiagnosisSession) -> None:
        """Save a diagnosis session.

        Args:
            session: The DiagnosisSession entity to save.
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a diagnosis session by ID.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            True if the session was deleted, False if not found.
        """
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Check if a diagnosis session exists.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            True if the session exists, False otherwise.
        """
        pass

