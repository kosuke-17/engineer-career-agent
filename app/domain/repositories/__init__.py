"""Domain repository interfaces."""

from .diagnosis_repository import DiagnosisRepository
from .learner_repository import LearnerRepository
from .roadmap_repository import RoadmapRepository
from .structured_diagnosis_repository import StructuredDiagnosisRepository

__all__ = [
    "LearnerRepository",
    "DiagnosisRepository",
    "RoadmapRepository",
    "StructuredDiagnosisRepository",
]
