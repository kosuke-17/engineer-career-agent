"""Domain repository interfaces."""

from .diagnosis_repository import DiagnosisRepository
from .structured_diagnosis_repository import StructuredDiagnosisRepository

__all__ = [
    "DiagnosisRepository",
    "StructuredDiagnosisRepository",
]
