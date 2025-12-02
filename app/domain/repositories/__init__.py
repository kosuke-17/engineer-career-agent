"""Domain repository interfaces."""

from .learner_repository import LearnerRepository
from .diagnosis_repository import DiagnosisRepository
from .roadmap_repository import RoadmapRepository

__all__ = [
    "LearnerRepository",
    "DiagnosisRepository",
    "RoadmapRepository",
]

