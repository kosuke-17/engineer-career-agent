"""API routes."""

from .diagnosis_router import router as diagnosis_router
from .profile_router import router as profile_router

__all__ = [
    "diagnosis_router",
    "profile_router",
]
