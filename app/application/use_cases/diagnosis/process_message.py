"""Process message use case."""

from app.application.dto import SendMessageRequest, SendMessageResponse
from app.application.services.llm_service import LLMServiceInterface
from app.domain.repositories import DiagnosisRepository


class ProcessMessageUseCase:
    """Use case for processing a message in a diagnosis session."""

    def __init__(
        self,
        diagnosis_repository: DiagnosisRepository,
        llm_service: LLMServiceInterface,
    ):
        self.diagnosis_repository = diagnosis_repository
        self.llm_service = llm_service

    async def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        """Execute the use case.

        Args:
            request: The send message request.

        Returns:
            SendMessageResponse with the response details.

        Raises:
            ValueError: If the session is not found.
        """
        # Find the session
        session = await self.diagnosis_repository.find_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Store the previous phase for comparison
        previous_phase = session.current_phase

        # Add user's message to the session
        session.add_message("user", request.message)

        # Process the message with LLM
        response, should_advance = await self.llm_service.process_message(
            session, request.message
        )

        # Add assistant's response to the session
        session.add_message("assistant", response)

        # Check if phase should advance
        if should_advance and not session.current_phase.is_final():
            # Get phase result from LLM
            phase_result = await self.llm_service.get_phase_result(session)
            session.complete_current_phase(result=phase_result)

        # Save the updated session
        await self.diagnosis_repository.save(session)

        return SendMessageResponse(
            session_id=session.id,
            response=response,
            current_phase=session.current_phase.value,
            phase_changed=session.current_phase != previous_phase,
            is_completed=session.is_completed,
            progress_percentage=session.get_progress_percentage(),
        )

