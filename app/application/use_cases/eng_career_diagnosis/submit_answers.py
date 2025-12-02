"""Submit answers use case."""

from dataclasses import dataclass, field
from typing import Any, Optional

from app.application.services.llm_service import LLMServiceInterface
from app.domain.constants import COMMON_QUESTIONS, get_domain_questions
from app.domain.entities import QuestionAnswer, StructuredDiagnosisPhase
from app.domain.repositories import StructuredDiagnosisRepository


@dataclass
class AnswerInput:
    """Input for a single answer."""

    question_id: str
    selected_options: list[str] = field(default_factory=list)


@dataclass
class SubmitAnswersRequest:
    """Request to submit answers."""

    session_id: str
    answers: list[AnswerInput] = field(default_factory=list)


@dataclass
class SubmitAnswersResponse:
    """Response after submitting answers."""

    session_id: str
    message: str
    current_phase: str
    phase_changed: bool = False
    is_completed: bool = False
    progress_percentage: float = 0.0
    questions: list[dict[str, Any]] = field(default_factory=list)
    roadmap: Optional[dict[str, Any]] = None


class SubmitAnswersUseCase:
    """Use case for submitting answers."""

    def __init__(
        self,
        repository: StructuredDiagnosisRepository,
        llm_service: LLMServiceInterface,
    ):
        self.repository = repository
        self.llm_service = llm_service

    async def execute(self, request: SubmitAnswersRequest) -> SubmitAnswersResponse:
        """Execute the use case.

        Args:
            request: The submit answers request.

        Returns:
            SubmitAnswersResponse with next questions or roadmap.

        Raises:
            ValueError: If session not found or invalid phase.
        """
        # Find the session
        session = await self.repository.find_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        previous_phase = session.current_phase

        # Process based on current phase
        if session.current_phase == StructuredDiagnosisPhase.COMMON_QUESTIONS:
            return await self._process_common_answers(session, request, previous_phase)
        elif session.current_phase == StructuredDiagnosisPhase.DOMAIN_QUESTIONS:
            return await self._process_domain_answers(session, request, previous_phase)
        else:
            raise ValueError(f"Cannot submit answers in phase: {session.current_phase.value}")

    async def _process_common_answers(
        self,
        session: Any,
        request: SubmitAnswersRequest,
        previous_phase: StructuredDiagnosisPhase,
    ) -> SubmitAnswersResponse:
        """Process answers to common questions."""
        # Create question lookup
        question_lookup = {q.id: q for q in COMMON_QUESTIONS}

        # Convert answers
        question_answers = []
        for answer in request.answers:
            question = question_lookup.get(answer.question_id)
            if question:
                # Get labels for selected options
                labels = []
                for opt in question.options:
                    if opt.id in answer.selected_options:
                        labels.append(opt.label)

                question_answers.append(
                    QuestionAnswer(
                        question_id=answer.question_id,
                        question_text=question.text,
                        selected_options=answer.selected_options,
                        selected_labels=labels,
                    )
                )

        # Add answers to session
        session.add_common_answers(question_answers)

        # Move to domain questions
        session.complete_common_questions()

        # Save the session
        await self.repository.save(session)

        # Get domain-specific questions
        domain_questions = get_domain_questions(session.selected_domain)
        questions_data = [q.to_dict() for q in domain_questions]

        return SubmitAnswersResponse(
            session_id=session.id,
            message="基本情報の入力が完了しました。次に、専門領域に関する質問にお答えください。",
            current_phase=session.current_phase.value,
            phase_changed=session.current_phase != previous_phase,
            is_completed=False,
            progress_percentage=session.get_progress_percentage(),
            questions=questions_data,
        )

    async def _process_domain_answers(
        self,
        session: Any,
        request: SubmitAnswersRequest,
        previous_phase: StructuredDiagnosisPhase,
    ) -> SubmitAnswersResponse:
        """Process answers to domain-specific questions."""
        # Create question lookup
        domain_questions = get_domain_questions(session.selected_domain)
        question_lookup = {q.id: q for q in domain_questions}

        # Convert answers
        question_answers = []
        for answer in request.answers:
            question = question_lookup.get(answer.question_id)
            if question:
                # Get labels for selected options
                labels = []
                for opt in question.options:
                    if opt.id in answer.selected_options:
                        labels.append(opt.label)

                question_answers.append(
                    QuestionAnswer(
                        question_id=answer.question_id,
                        question_text=question.text,
                        selected_options=answer.selected_options,
                        selected_labels=labels,
                    )
                )

        # Add answers to session
        session.add_domain_answers(question_answers)

        # Move to roadmap generation
        session.complete_domain_questions()

        # Generate roadmap using LLM
        context = session.get_context_for_roadmap()
        roadmap = await self.llm_service.generate_structured_roadmap(context)

        # Set roadmap and complete session
        session.set_roadmap(roadmap)

        # Save the session
        await self.repository.save(session)

        return SubmitAnswersResponse(
            session_id=session.id,
            message="診断が完了しました！あなた専用の学習ロードマップを生成しました。",
            current_phase=session.current_phase.value,
            phase_changed=session.current_phase != previous_phase,
            is_completed=True,
            progress_percentage=100.0,
            roadmap=roadmap,
        )

