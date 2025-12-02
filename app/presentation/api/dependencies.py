"""API dependencies for dependency injection."""

from functools import lru_cache

from app.application.services import LLMServiceInterface
from app.application.use_cases import (
    CreateProfileUseCase,
    DeleteProfileUseCase,
    GetDiagnosisResultUseCase,
    GetDiagnosisStatusUseCase,
    GetProfileUseCase,
    ProcessMessageUseCase,
    StartDiagnosisUseCase,
    UpdateProfileUseCase,
)
from app.config import get_settings
from app.domain.repositories import (
    DiagnosisRepository,
    LearnerRepository,
    RoadmapRepository,
)
from app.infrastructure.llm import LLMService
from app.infrastructure.persistence import (
    FileDiagnosisRepository,
    FileLearnerRepository,
    FileRoadmapRepository,
)


# Repository instances
@lru_cache
def get_learner_repository() -> LearnerRepository:
    """Get the learner repository instance."""
    settings = get_settings()
    return FileLearnerRepository(base_path=settings.memories_dir / "learners")


@lru_cache
def get_diagnosis_repository() -> DiagnosisRepository:
    """Get the diagnosis repository instance."""
    settings = get_settings()
    return FileDiagnosisRepository(base_path=settings.sessions_dir / "diagnosis")


@lru_cache
def get_roadmap_repository() -> RoadmapRepository:
    """Get the roadmap repository instance."""
    settings = get_settings()
    return FileRoadmapRepository(base_path=settings.memories_dir / "roadmaps")


# LLM Service instance
@lru_cache
def get_llm_service() -> LLMServiceInterface:
    """Get the LLM service instance."""
    return LLMService()


# Diagnosis Use Cases
def get_start_diagnosis_use_case() -> StartDiagnosisUseCase:
    """Get the start diagnosis use case."""
    return StartDiagnosisUseCase(
        learner_repository=get_learner_repository(),
        diagnosis_repository=get_diagnosis_repository(),
        llm_service=get_llm_service(),
    )


def get_process_message_use_case() -> ProcessMessageUseCase:
    """Get the process message use case."""
    return ProcessMessageUseCase(
        diagnosis_repository=get_diagnosis_repository(),
        llm_service=get_llm_service(),
    )


def get_diagnosis_status_use_case() -> GetDiagnosisStatusUseCase:
    """Get the diagnosis status use case."""
    return GetDiagnosisStatusUseCase(
        diagnosis_repository=get_diagnosis_repository(),
    )


def get_diagnosis_result_use_case() -> GetDiagnosisResultUseCase:
    """Get the diagnosis result use case."""
    return GetDiagnosisResultUseCase(
        diagnosis_repository=get_diagnosis_repository(),
        learner_repository=get_learner_repository(),
    )


# Profile Use Cases
def get_create_profile_use_case() -> CreateProfileUseCase:
    """Get the create profile use case."""
    return CreateProfileUseCase(
        learner_repository=get_learner_repository(),
    )


def get_get_profile_use_case() -> GetProfileUseCase:
    """Get the get profile use case."""
    return GetProfileUseCase(
        learner_repository=get_learner_repository(),
    )


def get_update_profile_use_case() -> UpdateProfileUseCase:
    """Get the update profile use case."""
    return UpdateProfileUseCase(
        learner_repository=get_learner_repository(),
    )


def get_delete_profile_use_case() -> DeleteProfileUseCase:
    """Get the delete profile use case."""
    return DeleteProfileUseCase(
        learner_repository=get_learner_repository(),
    )
