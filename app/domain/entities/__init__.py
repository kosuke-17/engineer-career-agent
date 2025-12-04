"""Domain entities."""

from .diagnosis import DiagnosisPhase, DiagnosisSession, Message, PhaseInfo
from .learning_roadmap import (
    LearningPhase,
    LearningRoadmap,
    LearningStep,
    SourceLink,
    TechnologyInfo,
    TechnologyRoadmap,
)
from .structured_diagnosis import (
    QuestionAnswer,
    StructuredDiagnosisPhase,
    StructuredDiagnosisSession,
)

__all__ = [
    "DiagnosisSession",
    "DiagnosisPhase",
    "PhaseInfo",
    "Message",
    "LearningPhase",
    "LearningRoadmap",
    "LearningStep",
    "SourceLink",
    "TechnologyInfo",
    "TechnologyRoadmap",
    "StructuredDiagnosisSession",
    "StructuredDiagnosisPhase",
    "QuestionAnswer",
]
