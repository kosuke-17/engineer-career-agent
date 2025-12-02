"""Engineer Career Diagnosis API router with predefined questions."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.use_cases.eng_career_diagnosis import (
    GetRoadmapUseCase,
    SelectDomainUseCase,
    SelectGoalUseCase,
    StartEngCareerDiagnosisUseCase,
    SubmitAnswersUseCase,
)
from app.application.use_cases.eng_career_diagnosis.select_domain import (
    SelectDomainRequest,
)
from app.application.use_cases.eng_career_diagnosis.select_goal import (
    SelectGoalRequest,
)
from app.application.use_cases.eng_career_diagnosis.start_diagnosis import (
    StartEngCareerDiagnosisRequest,
)
from app.application.use_cases.eng_career_diagnosis.submit_answers import (
    AnswerInput,
    SubmitAnswersRequest,
)
from app.presentation.api.dependencies import (
    get_eng_career_get_roadmap_use_case,
    get_eng_career_select_domain_use_case,
    get_eng_career_select_goal_use_case,
    get_eng_career_start_diagnosis_use_case,
    get_eng_career_submit_answers_use_case,
)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class DomainModel(BaseModel):
    """A domain option."""

    id: str
    label: str
    description: str


class GoalModel(BaseModel):
    """A goal option."""

    id: str
    label: str
    description: str


class QuestionOptionModel(BaseModel):
    """A single option for a question."""

    id: str
    label: str


class QuestionModel(BaseModel):
    """A structured question with options."""

    id: str
    text: str
    type: str
    category: str
    options: list[QuestionOptionModel]


class AnswerModel(BaseModel):
    """An answer to a question."""

    question_id: str
    selected_options: list[str]


# Start session
class StartSessionRequestModel(BaseModel):
    """Request to start a new engineer career diagnosis session."""

    user_id: Optional[str] = None


class StartSessionResponseModel(BaseModel):
    """Response after starting an engineer career diagnosis session."""

    session_id: str
    message: str
    current_phase: str
    domains: list[DomainModel]


# Select domain
class SelectDomainRequestModel(BaseModel):
    """Request to select a domain."""

    domain: str


class SelectDomainResponseModel(BaseModel):
    """Response after selecting a domain."""

    session_id: str
    message: str
    current_phase: str
    selected_domain: str
    goals: list[GoalModel]


# Select goal
class SelectGoalRequestModel(BaseModel):
    """Request to select a goal."""

    goal_id: str


class SelectGoalResponseModel(BaseModel):
    """Response after selecting a goal."""

    session_id: str
    message: str
    current_phase: str
    selected_goal: GoalModel
    questions: list[QuestionModel]


# Submit answers
class SubmitAnswersRequestModel(BaseModel):
    """Request to submit answers."""

    answers: list[AnswerModel]


class SubmitAnswersResponseModel(BaseModel):
    """Response after submitting answers."""

    session_id: str
    message: str
    current_phase: str
    phase_changed: bool
    is_completed: bool
    progress_percentage: float
    questions: list[QuestionModel] = []
    roadmap: Optional[dict[str, Any]] = None


# Get roadmap
class GetRoadmapResponseModel(BaseModel):
    """Response with roadmap details."""

    session_id: str
    is_completed: bool
    domain: Optional[str] = None
    goal: Optional[GoalModel] = None
    roadmap: Optional[dict[str, Any]] = None
    progress_percentage: float


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/start", response_model=StartSessionResponseModel)
async def start_diagnosis(
    request: StartSessionRequestModel,
    use_case: StartEngCareerDiagnosisUseCase = Depends(get_eng_career_start_diagnosis_use_case),
) -> StartSessionResponseModel:
    """Start a new engineer career diagnosis session.

    Returns domain options for selection.

    Args:
        request: The start session request.
        use_case: The start diagnosis use case.

    Returns:
        StartSessionResponseModel with session details and domain options.
    """
    dto_request = StartEngCareerDiagnosisRequest(user_id=request.user_id)
    result = await use_case.execute(dto_request)

    domains = [
        DomainModel(
            id=d["id"],
            label=d["label"],
            description=d["description"],
        )
        for d in result.domains
    ]

    return StartSessionResponseModel(
        session_id=result.session_id,
        message=result.message,
        current_phase=result.current_phase,
        domains=domains,
    )


@router.post("/{session_id}/domain", response_model=SelectDomainResponseModel)
async def select_domain(
    session_id: str,
    request: SelectDomainRequestModel,
    use_case: SelectDomainUseCase = Depends(get_eng_career_select_domain_use_case),
) -> SelectDomainResponseModel:
    """Select a domain for the diagnosis.

    Returns goal options for selection.

    Args:
        session_id: The session ID.
        request: The select domain request.
        use_case: The select domain use case.

    Returns:
        SelectDomainResponseModel with goal options.

    Raises:
        HTTPException: If session not found or invalid domain.
    """
    try:
        dto_request = SelectDomainRequest(
            session_id=session_id,
            domain=request.domain,
        )
        result = await use_case.execute(dto_request)

        goals = [
            GoalModel(
                id=g["id"],
                label=g["label"],
                description=g["description"],
            )
            for g in result.goals
        ]

        return SelectDomainResponseModel(
            session_id=result.session_id,
            message=result.message,
            current_phase=result.current_phase,
            selected_domain=result.selected_domain,
            goals=goals,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/goal", response_model=SelectGoalResponseModel)
async def select_goal(
    session_id: str,
    request: SelectGoalRequestModel,
    use_case: SelectGoalUseCase = Depends(get_eng_career_select_goal_use_case),
) -> SelectGoalResponseModel:
    """Select a goal for the diagnosis.

    Returns common questions for answering.

    Args:
        session_id: The session ID.
        request: The select goal request.
        use_case: The select goal use case.

    Returns:
        SelectGoalResponseModel with common questions.

    Raises:
        HTTPException: If session not found or invalid goal.
    """
    try:
        dto_request = SelectGoalRequest(
            session_id=session_id,
            goal_id=request.goal_id,
        )
        result = await use_case.execute(dto_request)

        questions = [
            QuestionModel(
                id=q["id"],
                text=q["text"],
                type=q["type"],
                category=q["category"],
                options=[
                    QuestionOptionModel(id=opt["id"], label=opt["label"]) for opt in q["options"]
                ],
            )
            for q in result.questions
        ]

        selected_goal = GoalModel(
            id=result.selected_goal["id"],
            label=result.selected_goal["label"],
            description=result.selected_goal["description"],
        )

        return SelectGoalResponseModel(
            session_id=result.session_id,
            message=result.message,
            current_phase=result.current_phase,
            selected_goal=selected_goal,
            questions=questions,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/answers", response_model=SubmitAnswersResponseModel)
async def submit_answers(
    session_id: str,
    request: SubmitAnswersRequestModel,
    use_case: SubmitAnswersUseCase = Depends(get_eng_career_submit_answers_use_case),
) -> SubmitAnswersResponseModel:
    """Submit answers to questions.

    Returns next set of questions or generated roadmap.

    Args:
        session_id: The session ID.
        request: The submit answers request.
        use_case: The submit answers use case.

    Returns:
        SubmitAnswersResponseModel with next questions or roadmap.

    Raises:
        HTTPException: If session not found or invalid phase.
    """
    try:
        answers = [
            AnswerInput(
                question_id=a.question_id,
                selected_options=a.selected_options,
            )
            for a in request.answers
        ]

        dto_request = SubmitAnswersRequest(
            session_id=session_id,
            answers=answers,
        )
        result = await use_case.execute(dto_request)

        questions = [
            QuestionModel(
                id=q["id"],
                text=q["text"],
                type=q["type"],
                category=q["category"],
                options=[
                    QuestionOptionModel(id=opt["id"], label=opt["label"]) for opt in q["options"]
                ],
            )
            for q in result.questions
        ]

        return SubmitAnswersResponseModel(
            session_id=result.session_id,
            message=result.message,
            current_phase=result.current_phase,
            phase_changed=result.phase_changed,
            is_completed=result.is_completed,
            progress_percentage=result.progress_percentage,
            questions=questions,
            roadmap=result.roadmap,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/roadmap", response_model=GetRoadmapResponseModel)
async def get_roadmap(
    session_id: str,
    use_case: GetRoadmapUseCase = Depends(get_eng_career_get_roadmap_use_case),
) -> GetRoadmapResponseModel:
    """Get the generated roadmap for a session.

    Args:
        session_id: The session ID.
        use_case: The get roadmap use case.

    Returns:
        GetRoadmapResponseModel with roadmap details.

    Raises:
        HTTPException: If session not found.
    """
    try:
        result = await use_case.execute(session_id)

        goal = None
        if result.goal:
            goal = GoalModel(
                id=result.goal["id"],
                label=result.goal["label"],
                description="",  # Description not stored in session
            )

        return GetRoadmapResponseModel(
            session_id=result.session_id,
            is_completed=result.is_completed,
            domain=result.domain,
            goal=goal,
            roadmap=result.roadmap,
            progress_percentage=result.progress_percentage,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
