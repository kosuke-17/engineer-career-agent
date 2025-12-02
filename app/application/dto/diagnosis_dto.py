"""Diagnosis DTOs."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StartDiagnosisRequest:
    """Request to start a new diagnosis session."""

    user_id: Optional[str] = None


@dataclass
class StartDiagnosisResponse:
    """Response after starting a diagnosis session."""

    session_id: str
    message: str
    current_phase: str
    phases: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SendMessageRequest:
    """Request to send a message in a diagnosis session."""

    session_id: str
    message: str


@dataclass
class SendMessageResponse:
    """Response after processing a message."""

    session_id: str
    response: str
    current_phase: str
    phase_changed: bool = False
    is_completed: bool = False
    progress_percentage: float = 0.0


@dataclass
class DiagnosisStatusResponse:
    """Response with diagnosis session status."""

    session_id: str
    user_id: Optional[str]
    current_phase: str
    is_completed: bool
    progress_percentage: float
    phases: dict[str, dict[str, Any]] = field(default_factory=dict)
    message_count: int = 0


@dataclass
class DiagnosisResultResponse:
    """Response with diagnosis results."""

    session_id: str
    user_id: Optional[str]
    is_completed: bool
    skill_scores: list[dict[str, Any]] = field(default_factory=list)
    domain_aptitudes: list[dict[str, Any]] = field(default_factory=list)
    roadmap: Optional[dict[str, Any]] = None
    summary: Optional[str] = None

