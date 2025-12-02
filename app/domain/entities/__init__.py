"""Domain entities."""

from .diagnosis import DiagnosisSession, DiagnosisPhase, PhaseInfo, Message
from .structured_diagnosis import (
    StructuredDiagnosisSession,
    StructuredDiagnosisPhase,
    QuestionAnswer,
)

__all__ = [
    "DiagnosisSession",
    "DiagnosisPhase",
    "PhaseInfo",
    "Message",
    "StructuredDiagnosisSession",
    "StructuredDiagnosisPhase",
    "QuestionAnswer",
]
