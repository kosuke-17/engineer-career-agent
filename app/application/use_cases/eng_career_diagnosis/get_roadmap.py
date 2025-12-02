"""Get roadmap use case."""

from dataclasses import dataclass
from typing import Any, Optional

from app.domain.repositories import StructuredDiagnosisRepository


@dataclass
class GetRoadmapResponse:
    """Response with roadmap details."""

    session_id: str
    is_completed: bool
    domain: Optional[str] = None
    goal: Optional[dict[str, Any]] = None
    roadmap: Optional[dict[str, Any]] = None
    progress_percentage: float = 0.0


class GetRoadmapUseCase:
    """Use case for getting the roadmap."""

    def __init__(self, repository: StructuredDiagnosisRepository):
        self.repository = repository

    async def execute(self, session_id: str) -> GetRoadmapResponse:
        """Execute the use case.

        Args:
            session_id: The session ID.

        Returns:
            GetRoadmapResponse with roadmap details.

        Raises:
            ValueError: If session not found.
        """
        # Find the session
        session = await self.repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        goal = None
        if session.selected_goal_id:
            goal = {
                "id": session.selected_goal_id,
                "label": session.selected_goal_label,
            }

        return GetRoadmapResponse(
            session_id=session.id,
            is_completed=session.is_completed,
            domain=session.selected_domain,
            goal=goal,
            roadmap=session.roadmap,
            progress_percentage=session.get_progress_percentage(),
        )
