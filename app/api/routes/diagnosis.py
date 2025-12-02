"""Diagnosis API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.agents.main_agent import LearningPathAgent
from app.config import Settings, get_settings
from app.models.diagnosis import (
    DiagnosisMessageResponse,
    DiagnosisPhase,
    DiagnosisStatusResponse,
    SendMessageRequest,
    StartDiagnosisRequest,
)

router = APIRouter()

# Global agent instance (in production, use dependency injection with proper lifecycle)
_agent: Optional[LearningPathAgent] = None


def get_agent(settings: Settings = Depends(get_settings)) -> LearningPathAgent:
    """Get or create the learning path agent."""
    global _agent
    if _agent is None:
        _agent = LearningPathAgent()
    return _agent


@router.post("/start", response_model=dict)
async def start_diagnosis(
    request: StartDiagnosisRequest,
    agent: LearningPathAgent = Depends(get_agent),
) -> dict:
    """
    Start a new diagnosis session.

    Args:
        request: Request containing user_id and optional initial message

    Returns:
        Session ID and initial response from the agent
    """
    try:
        session_id, response = await agent.start_session(
            user_id=request.user_id,
            initial_message=request.initial_message,
        )

        return {
            "session_id": session_id,
            "user_id": request.user_id,
            "message": response,
            "current_phase": DiagnosisPhase.FOUNDATION.value,
            "phase_name": "基礎スキル診断",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/message", response_model=DiagnosisMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    agent: LearningPathAgent = Depends(get_agent),
) -> DiagnosisMessageResponse:
    """
    Send a message in an existing diagnosis session.

    Args:
        session_id: Session identifier
        request: Request containing user message

    Returns:
        Assistant response and session status
    """
    try:
        response = await agent.process_message(
            session_id=session_id,
            user_message=request.message,
        )

        status = await agent.get_session_status(session_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return DiagnosisMessageResponse(
            session_id=session_id,
            assistant_message=response,
            current_phase=DiagnosisPhase(status["current_phase"]),
            phase_name=status["phase_name"],
            is_complete=status["is_complete"],
            todos=status.get("todos", {}).get("todos"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/status", response_model=DiagnosisStatusResponse)
async def get_diagnosis_status(
    session_id: str,
    agent: LearningPathAgent = Depends(get_agent),
) -> DiagnosisStatusResponse:
    """
    Get the status of a diagnosis session.

    Args:
        session_id: Session identifier

    Returns:
        Current session status including phase and progress
    """
    try:
        status = await agent.get_session_status(session_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return DiagnosisStatusResponse(
            session_id=session_id,
            current_phase=DiagnosisPhase(status["current_phase"]),
            phase_name=status["phase_name"],
            phase_description="",  # Could be enhanced
            phases_completed=status["phases_completed"],
            total_phases=status["total_phases"],
            is_complete=status["is_complete"],
            progress_percentage=status["progress_percentage"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/result")
async def get_diagnosis_result(
    session_id: str,
    agent: LearningPathAgent = Depends(get_agent),
) -> dict:
    """
    Get the complete result of a diagnosis session.

    Args:
        session_id: Session identifier

    Returns:
        Complete assessment results including roadmap
    """
    try:
        result = await agent.get_session_result(session_id)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/advance-phase")
async def advance_phase(
    session_id: str,
    agent: LearningPathAgent = Depends(get_agent),
) -> dict:
    """
    Manually advance to the next diagnosis phase.

    Args:
        session_id: Session identifier

    Returns:
        Success status and message
    """
    try:
        success, message = await agent.advance_phase(session_id)

        if not success and "見つかりません" in message:
            raise HTTPException(status_code=404, detail=message)

        return {
            "success": success,
            "message": message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/todos")
async def get_session_todos(
    session_id: str,
    agent: LearningPathAgent = Depends(get_agent),
) -> dict:
    """
    Get the todo list for a diagnosis session.

    Args:
        session_id: Session identifier

    Returns:
        Todo list with progress
    """
    try:
        display = agent.get_todo_display(session_id)
        status = await agent.get_session_status(session_id)

        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return {
            "session_id": session_id,
            "display": display,
            "todos": status.get("todos"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
