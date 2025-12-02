"""Structured diagnosis repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities import StructuredDiagnosisSession


class StructuredDiagnosisRepository(ABC):
    """Repository interface for structured diagnosis sessions."""

    @abstractmethod
    async def save(self, session: StructuredDiagnosisSession) -> None:
        """Save a diagnosis session.

        Args:
            session: The session to save.
        """
        pass

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[StructuredDiagnosisSession]:
        """Find a session by ID.

        Args:
            session_id: The session ID.

        Returns:
            The session if found, None otherwise.
        """
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> list[StructuredDiagnosisSession]:
        """Find all sessions for a user.

        Args:
            user_id: The user ID.

        Returns:
            List of sessions for the user.
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: The session ID.

        Returns:
            True if deleted, False if not found.
        """
        pass

