"""Get diagnosis status use case."""

from app.application.dto import DiagnosisStatusResponse
from app.domain.repositories import DiagnosisRepository


class GetDiagnosisStatusUseCase:
    """Use case for getting diagnosis session status."""

    def __init__(self, diagnosis_repository: DiagnosisRepository):
        self.diagnosis_repository = diagnosis_repository

    async def execute(self, session_id: str) -> DiagnosisStatusResponse:
        """Execute the use case.

        Args:
            session_id: The session ID.

        Returns:
            DiagnosisStatusResponse with status details.

        Raises:
            ValueError: If the session is not found.
        """
        session = await self.diagnosis_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        phases = {}
        for name, info in session.phases.items():
            phases[name] = {
                "status": info.status.value,
                "started_at": info.started_at.isoformat() if info.started_at else None,
                "completed_at": info.completed_at.isoformat() if info.completed_at else None,
                "has_result": info.result is not None,
            }

        return DiagnosisStatusResponse(
            session_id=session.id,
            user_id=session.user_id,
            current_phase=session.current_phase.value,
            is_completed=session.is_completed,
            progress_percentage=session.get_progress_percentage(),
            phases=phases,
            message_count=len(session.messages),
        )

