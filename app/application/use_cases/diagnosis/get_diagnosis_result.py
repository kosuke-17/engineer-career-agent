"""Get diagnosis result use case."""

from typing import Any

from app.application.dto import DiagnosisResultResponse
from app.domain.repositories import DiagnosisRepository, LearnerRepository


class GetDiagnosisResultUseCase:
    """Use case for getting diagnosis results."""

    def __init__(
        self,
        diagnosis_repository: DiagnosisRepository,
        learner_repository: LearnerRepository,
    ):
        self.diagnosis_repository = diagnosis_repository
        self.learner_repository = learner_repository

    async def execute(self, session_id: str) -> DiagnosisResultResponse:
        """Execute the use case.

        Args:
            session_id: The session ID.

        Returns:
            DiagnosisResultResponse with diagnosis results.

        Raises:
            ValueError: If the session is not found.
        """
        session = await self.diagnosis_repository.find_by_id(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Collect results from all completed phases
        skill_scores: list[dict[str, Any]] = []
        domain_aptitudes: list[dict[str, Any]] = []
        roadmap: dict[str, Any] | None = None
        summary = None

        for phase_info in session.get_completed_phases():
            if phase_info.result:
                # Extract skill scores
                if "skills" in phase_info.result:
                    for skill in phase_info.result["skills"]:
                        skill_scores.append(skill)

                # Extract domain aptitudes
                if "aptitudes" in phase_info.result:
                    for aptitude in phase_info.result["aptitudes"]:
                        domain_aptitudes.append(aptitude)

                # Extract roadmap
                if "roadmap" in phase_info.result:
                    roadmap = phase_info.result["roadmap"]

                # Extract summary
                if "summary" in phase_info.result:
                    summary = phase_info.result["summary"]

        # If learner exists, get their stored data as well
        if session.user_id:
            learner = await self.learner_repository.find_by_id(session.user_id)
            if learner:
                # Merge stored skill scores
                for score in learner.skill_scores:
                    skill_scores.append({
                        "name": score.skill_name,
                        "score": score.score,
                        "level": score.level.value,
                        "notes": score.notes,
                    })

                # Merge stored domain aptitudes
                for aptitude in learner.domain_aptitudes:
                    domain_aptitudes.append({
                        "domain": aptitude.domain.value,
                        "score": aptitude.score,
                        "reasoning": aptitude.reasoning,
                    })

        return DiagnosisResultResponse(
            session_id=session.id,
            user_id=session.user_id,
            is_completed=session.is_completed,
            skill_scores=skill_scores,
            domain_aptitudes=domain_aptitudes,
            roadmap=roadmap,
            summary=summary,
        )

