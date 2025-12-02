"""Data Transfer Objects."""

from .diagnosis_dto import (
    StartDiagnosisRequest,
    StartDiagnosisResponse,
    SendMessageRequest,
    SendMessageResponse,
    DiagnosisStatusResponse,
    DiagnosisResultResponse,
)
from .profile_dto import (
    CreateProfileRequest,
    UpdateProfileRequest,
    ProfileResponse,
)

__all__ = [
    "StartDiagnosisRequest",
    "StartDiagnosisResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    "DiagnosisStatusResponse",
    "DiagnosisResultResponse",
    "CreateProfileRequest",
    "UpdateProfileRequest",
    "ProfileResponse",
]

