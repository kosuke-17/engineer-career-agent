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

        # Generate initial structured response from LLM
        initial_response = await self.llm_service.generate_initial_response(session)

        # Convert questions to dict format for storage
        questions_data = [
            {
                "id": q.id,
                "text": q.text,
                "type": q.type,
                "options": [{"id": opt.id, "label": opt.label} for opt in q.options],
            }
            for q in initial_response.questions
        ]

        # Add assistant's message to the session with questions
        session.add_message(
            role="assistant",
            content=initial_response.message,
            questions=questions_data,
        )

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
            message=initial_response.message,
            questions=initial_response.questions,
            current_phase=session.current_phase.value,
            phases=phases,
        )
