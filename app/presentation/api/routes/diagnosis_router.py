"""Diagnosis API router."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.dto import (
    SendMessageRequest,
    StartDiagnosisRequest,
)
from app.application.use_cases import (
    GetDiagnosisResultUseCase,
    GetDiagnosisStatusUseCase,
    ProcessMessageUseCase,
    StartDiagnosisUseCase,
)
from app.presentation.api.dependencies import (
    get_diagnosis_result_use_case,
    get_diagnosis_status_use_case,
    get_process_message_use_case,
    get_start_diagnosis_use_case,
)

router = APIRouter()


# Request/Response models for API
class StartSessionRequest(BaseModel):
    """Request to start a new diagnosis session."""

    user_id: Optional[str] = None


class StartSessionResponse(BaseModel):
    """Response after starting a diagnosis session."""

    session_id: str
    message: str
    current_phase: str
    phases: list[dict[str, Any]]


class SendMessageRequestModel(BaseModel):
    """Request to send a message."""

    message: str


class SendMessageResponseModel(BaseModel):
    """Response after sending a message."""

    session_id: str
    content: str
    current_phase: str
    phase_changed: bool
    is_completed: bool
    progress_percentage: float


class SessionStatusResponse(BaseModel):
    """Response with session status."""

    session_id: str
    user_id: Optional[str]
    current_phase: str
    is_completed: bool
    progress_percentage: float
    phases: dict[str, dict[str, Any]]
    message_count: int


class DiagnosisResultResponseModel(BaseModel):
    """Response with diagnosis results."""

    session_id: str
    user_id: Optional[str]
    is_completed: bool
    skill_scores: list[dict[str, Any]]
    domain_aptitudes: list[dict[str, Any]]
    roadmap: Optional[dict[str, Any]]
    summary: Optional[str]


@router.post("/start", response_model=StartSessionResponse)
async def start_diagnosis(
    request: StartSessionRequest,
    use_case: StartDiagnosisUseCase = Depends(get_start_diagnosis_use_case),
) -> StartSessionResponse:
    """Start a new diagnosis session.

    Args:
        request: The start session request.
        use_case: The start diagnosis use case.

    Returns:
        StartSessionResponse with session details.
    """
    dto_request = StartDiagnosisRequest(user_id=request.user_id)
    result = await use_case.execute(dto_request)

    return StartSessionResponse(
        session_id=result.session_id,
        message=result.message,
        current_phase=result.current_phase,
        phases=result.phases,
    )


@router.post("/{session_id}/message", response_model=SendMessageResponseModel)
async def send_message(
    session_id: str,
    request: SendMessageRequestModel,
    use_case: ProcessMessageUseCase = Depends(get_process_message_use_case),
) -> SendMessageResponseModel:
    """Send a message in a diagnosis session.

    Args:
        session_id: The session ID.
        request: The message request.
        use_case: The process message use case.

    Returns:
        SendMessageResponseModel with the response.

    Raises:
        HTTPException: If the session is not found.
    """
    try:
        dto_request = SendMessageRequest(
            session_id=session_id,
            message=request.message,
        )
        result = await use_case.execute(dto_request)

        return SendMessageResponseModel(
            session_id=result.session_id,
            content=result.response,
            current_phase=result.current_phase,
            phase_changed=result.phase_changed,
            is_completed=result.is_completed,
            progress_percentage=result.progress_percentage,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_status(
    session_id: str,
    use_case: GetDiagnosisStatusUseCase = Depends(get_diagnosis_status_use_case),
) -> SessionStatusResponse:
    """Get the status of a diagnosis session.

    Args:
        session_id: The session ID.
        use_case: The get diagnosis status use case.

    Returns:
        SessionStatusResponse with status details.

    Raises:
        HTTPException: If the session is not found.
    """
    try:
        result = await use_case.execute(session_id)

        return SessionStatusResponse(
            session_id=result.session_id,
            user_id=result.user_id,
            current_phase=result.current_phase,
            is_completed=result.is_completed,
            progress_percentage=result.progress_percentage,
            phases=result.phases,
            message_count=result.message_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{session_id}/result", response_model=DiagnosisResultResponseModel)
async def get_result(
    session_id: str,
    use_case: GetDiagnosisResultUseCase = Depends(get_diagnosis_result_use_case),
) -> DiagnosisResultResponseModel:
    """Get the result of a diagnosis session.

    Args:
        session_id: The session ID.
        use_case: The get diagnosis result use case.

    Returns:
        DiagnosisResultResponseModel with diagnosis results.

    Raises:
        HTTPException: If the session is not found.
    """
    try:
        result = await use_case.execute(session_id)

        return DiagnosisResultResponseModel(
            session_id=result.session_id,
            user_id=result.user_id,
            is_completed=result.is_completed,
            skill_scores=result.skill_scores,
            domain_aptitudes=result.domain_aptitudes,
            roadmap=result.roadmap,
            summary=result.summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
