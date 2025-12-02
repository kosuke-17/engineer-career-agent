"""Start engineer career diagnosis use case."""

from dataclasses import dataclass, field
from typing import Any, Optional

from app.domain.constants import DOMAINS
from app.domain.entities import StructuredDiagnosisSession
from app.domain.repositories import StructuredDiagnosisRepository


@dataclass
class StartEngCareerDiagnosisRequest:
    """Request to start a new engineer career diagnosis session."""

    user_id: Optional[str] = None


@dataclass
class StartEngCareerDiagnosisResponse:
    """Response after starting an engineer career diagnosis session."""

    session_id: str
    message: str
    current_phase: str
    domains: list[dict[str, Any]] = field(default_factory=list)


class StartEngCareerDiagnosisUseCase:
    """Use case for starting a new engineer career diagnosis session."""

    def __init__(self, repository: StructuredDiagnosisRepository):
        self.repository = repository

    async def execute(
        self, request: StartEngCareerDiagnosisRequest
    ) -> StartEngCareerDiagnosisResponse:
        """Execute the use case.

        Args:
            request: The start diagnosis request.

        Returns:
            StartEngCareerDiagnosisResponse with session details and domain options.
        """
        # Create a new structured diagnosis session
        session = StructuredDiagnosisSession.create(user_id=request.user_id)

        # Save the session
        await self.repository.save(session)

        return StartEngCareerDiagnosisResponse(
            session_id=session.id,
            message="診断を開始します。まず、専門としたい領域を選択してください。",
            current_phase=session.current_phase.value,
            domains=DOMAINS,
        )

