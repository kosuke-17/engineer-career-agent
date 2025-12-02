"""Select goal use case."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.constants import COMMON_QUESTIONS, get_goals_for_domain
from app.domain.repositories import StructuredDiagnosisRepository


@dataclass
class SelectGoalRequest:
    """Request to select a goal."""

    session_id: str
    goal_id: str


@dataclass
class SelectGoalResponse:
    """Response after selecting a goal."""

    session_id: str
    message: str
    current_phase: str
    selected_goal: dict[str, Any] = field(default_factory=dict)
    questions: list[dict[str, Any]] = field(default_factory=list)


class SelectGoalUseCase:
    """Use case for selecting a goal."""

    def __init__(self, repository: StructuredDiagnosisRepository):
        self.repository = repository

    async def execute(self, request: SelectGoalRequest) -> SelectGoalResponse:
        """Execute the use case.

        Args:
            request: The select goal request.

        Returns:
            SelectGoalResponse with common questions.

        Raises:
            ValueError: If session not found or invalid goal.
        """
        # Find the session
        session = await self.repository.find_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Verify domain is selected
        if not session.selected_domain:
            raise ValueError("Domain must be selected before goal")

        # Get goals for the domain and validate
        goals = get_goals_for_domain(session.selected_domain)
        selected_goal = None
        for goal in goals:
            if goal.id == request.goal_id:
                selected_goal = goal
                break

        if not selected_goal:
            valid_goal_ids = [g.id for g in goals]
            raise ValueError(f"Invalid goal: {request.goal_id}. Must be one of: {valid_goal_ids}")

        # Select goal
        session.select_goal(selected_goal.id, selected_goal.label)

        # Save the session
        await self.repository.save(session)

        # Get common questions
        questions_data = [q.to_dict() for q in COMMON_QUESTIONS]

        return SelectGoalResponse(
            session_id=session.id,
            message=f"「{selected_goal.label}」を選択しました。まず、基本的な情報をお聞きします。",
            current_phase=session.current_phase.value,
            selected_goal=selected_goal.to_dict(),
            questions=questions_data,
        )

