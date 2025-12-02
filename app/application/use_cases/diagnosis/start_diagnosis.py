"""Start diagnosis use case."""

from app.application.dto import StartDiagnosisRequest, StartDiagnosisResponse
from app.application.services.llm_service import LLMServiceInterface
from app.domain.entities import DiagnosisSession
from app.domain.repositories import DiagnosisRepository, LearnerRepository
from app.domain.value_objects import Phase


class StartDiagnosisUseCase:
    """Use case for starting a new diagnosis session."""

    def __init__(
        self,
        learner_repository: LearnerRepository,
        diagnosis_repository: DiagnosisRepository,
        llm_service: LLMServiceInterface,
    ):
        self.learner_repository = learner_repository
        self.diagnosis_repository = diagnosis_repository
        self.llm_service = llm_service

    async def execute(self, request: StartDiagnosisRequest) -> StartDiagnosisResponse:
        """Execute the use case.

        Args:
            request: The start diagnosis request.

        Returns:
            StartDiagnosisResponse with session details.
        """
        # Create a new diagnosis session
        session = DiagnosisSession.create(user_id=request.user_id)

        # Generate initial message from LLM
        initial_message = await self.llm_service.generate_initial_message(session)

        # Add assistant's message to the session
        session.add_message("assistant", initial_message)

        # Save the session
        await self.diagnosis_repository.save(session)

        # Prepare phase information
        phases = [
            {
                "phase": phase.value,
                "name": phase.display_name,
                "description": phase.description,
                "order": phase.order,
            }
            for phase in Phase
        ]

        return StartDiagnosisResponse(
            session_id=session.id,
            message=initial_message,
            current_phase=session.current_phase.value,
            phases=phases,
        )

