"""LLM service interface for application layer."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.application.dto import Answer, StructuredResponse
from app.domain.entities import DiagnosisSession


class LLMServiceInterface(ABC):
    """Abstract interface for LLM service.

    This interface is defined in the application layer and
    implemented in the infrastructure layer.
    """

    @abstractmethod
    async def generate_initial_response(self, session: DiagnosisSession) -> StructuredResponse:
        """Generate the initial response for a diagnosis session.

        Args:
            session: The diagnosis session.

        Returns:
            A StructuredResponse containing message and questions.
        """
        pass

    @abstractmethod
    async def process_answers(
        self, session: DiagnosisSession, answers: list[Answer], supplement: Optional[str]
    ) -> StructuredResponse:
        """Process user answers and generate a response.

        Args:
            session: The diagnosis session.
            answers: The user's answers to questions.
            supplement: Optional supplementary text from the user.

        Returns:
            A StructuredResponse containing message, questions, and should_advance flag.
        """
        pass

    @abstractmethod
    async def get_phase_result(self, session: DiagnosisSession) -> Optional[dict[str, Any]]:
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

    @abstractmethod
    async def generate_structured_roadmap(
        self,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a learning roadmap from structured diagnosis context.

        Args:
            context: The diagnosis context containing:
                - domain: Selected domain (frontend/backend/infrastructure)
                - goal: Selected goal with id and label
                - common_answers: List of common question answers
                - domain_answers: List of domain-specific question answers

        Returns:
            A dictionary containing the structured roadmap with:
                - goal: The learning goal
                - domain: The selected domain
                - duration_months: Total duration
                - phases: List of learning phases
                - milestones: Key milestones
                - final_project: Suggested final project
        """
        pass
