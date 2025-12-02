"""LLM service interface for application layer."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.domain.entities import DiagnosisSession


class LLMServiceInterface(ABC):
    """Abstract interface for LLM service.

    This interface is defined in the application layer and
    implemented in the infrastructure layer.
    """

    @abstractmethod
    async def generate_initial_message(
        self, session: DiagnosisSession
    ) -> str:
        """Generate the initial message for a diagnosis session.

        Args:
            session: The diagnosis session.

        Returns:
            The initial message string.
        """
        pass

    @abstractmethod
    async def process_message(
        self, session: DiagnosisSession, user_message: str
    ) -> tuple[str, bool]:
        """Process a user message and generate a response.

        Args:
            session: The diagnosis session.
            user_message: The user's message.

        Returns:
            A tuple of (response_message, should_advance_phase).
        """
        pass

    @abstractmethod
    async def get_phase_result(
        self, session: DiagnosisSession
    ) -> Optional[dict[str, Any]]:
        """Get the result of the current phase.

        Args:
            session: The diagnosis session.

        Returns:
            A dictionary containing the phase result, or None.
        """
        pass

    @abstractmethod
    async def generate_roadmap(
        self,
        session: DiagnosisSession,
        skill_scores: list[dict[str, Any]],
        domain_aptitudes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate a learning roadmap based on diagnosis results.

        Args:
            session: The diagnosis session.
            skill_scores: List of skill score dictionaries.
            domain_aptitudes: List of domain aptitude dictionaries.

        Returns:
            A dictionary containing the roadmap data.
        """
        pass

