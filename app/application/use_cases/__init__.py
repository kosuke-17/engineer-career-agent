"""Application use cases."""

from .diagnosis import (
    GetDiagnosisResultUseCase,
    GetDiagnosisStatusUseCase,
    ProcessMessageUseCase,
    StartDiagnosisUseCase,
)
from .eng_career_diagnosis import (
    GetRoadmapUseCase,
    SelectDomainUseCase,
    SelectGoalUseCase,
    StartEngCareerDiagnosisUseCase,
    SubmitAnswersUseCase,
)
from .profile import (
    CreateProfileUseCase,
    DeleteProfileUseCase,
    GetProfileUseCase,
    UpdateProfileUseCase,
)

__all__ = [
    # Legacy Diagnosis
    "StartDiagnosisUseCase",
    "ProcessMessageUseCase",
    "GetDiagnosisStatusUseCase",
    "GetDiagnosisResultUseCase",
    # Profile
    "CreateProfileUseCase",
    "GetProfileUseCase",
    "UpdateProfileUseCase",
    "DeleteProfileUseCase",
    # Engineer Career Diagnosis
    "StartEngCareerDiagnosisUseCase",
    "SelectDomainUseCase",
    "SelectGoalUseCase",
    "SubmitAnswersUseCase",
    "GetRoadmapUseCase",
]
