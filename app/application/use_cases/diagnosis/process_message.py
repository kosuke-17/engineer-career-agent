"""Process message use case."""

from app.application.dto import SendMessageRequest, SendMessageResponse
from app.application.services.llm_service import LLMServiceInterface
from app.domain.repositories import DiagnosisRepository


class ProcessMessageUseCase:
    """Use case for processing answers in a diagnosis session."""

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
            request: The send message request containing answers.

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

        # Convert answers to dict format for storage
        answers_data = [
            {
                "question_id": answer.question_id,
                "selected_options": answer.selected_options,
            }
            for answer in request.answers
        ]

        # Build content summary from answers
        content_parts = []
        for answer in request.answers:
            selected = ", ".join(answer.selected_options)
            content_parts.append(f"{answer.question_id}: {selected}")
        if request.supplement:
            content_parts.append(f"補足: {request.supplement}")
        content_summary = "\n".join(content_parts)

        # Add user's answers to the session
        session.add_message(
            role="user",
            content=content_summary,
            answers=answers_data,
        )

        # Process the answers with LLM
        structured_response = await self.llm_service.process_answers(
            session, request.answers, request.supplement
        )

        # Convert questions to dict format for storage
        questions_data = [
            {
                "id": q.id,
                "text": q.text,
                "type": q.type,
                "options": [{"id": opt.id, "label": opt.label} for opt in q.options],
            }
            for q in structured_response.questions
        ]

        # Add assistant's response to the session
        session.add_message(
            role="assistant",
            content=structured_response.message,
            questions=questions_data,
        )

        # Check if phase should advance
        if structured_response.should_advance and not session.current_phase.is_final():
            # Get phase result from LLM
            phase_result = await self.llm_service.get_phase_result(session)
            session.complete_current_phase(result=phase_result)

        # Save the updated session
        await self.diagnosis_repository.save(session)

        return SendMessageResponse(
            session_id=session.id,
            message=structured_response.message,
            questions=structured_response.questions,
            current_phase=session.current_phase.value,
            phase_changed=session.current_phase != previous_phase,
            is_completed=session.is_completed,
            progress_percentage=session.get_progress_percentage(),
        )
