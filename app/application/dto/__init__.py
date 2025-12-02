"""Data Transfer Objects."""

from .diagnosis_dto import (
    Answer,
    DiagnosisResultResponse,
    DiagnosisStatusResponse,
    Question,
    QuestionOption,
    SendMessageRequest,
    SendMessageResponse,
    StartDiagnosisRequest,
    StartDiagnosisResponse,
    StructuredResponse,
)
from .profile_dto import (
    CreateProfileRequest,
    ProfileResponse,
    UpdateProfileRequest,
)

__all__ = [
    "Answer",
    "CreateProfileRequest",
    "DiagnosisResultResponse",
    "DiagnosisStatusResponse",
    "ProfileResponse",
    "Question",
    "QuestionOption",
    "SendMessageRequest",
    "SendMessageResponse",
    "StartDiagnosisRequest",
    "StartDiagnosisResponse",
    "StructuredResponse",
    "UpdateProfileRequest",
]
