"""API dependencies for dependency injection."""

from functools import lru_cache

from app.application.services import LLMServiceInterface
from app.application.use_cases import (
    GetRoadmapUseCase,
    SelectDomainUseCase,
    SelectGoalUseCase,
    # Engineer Career Diagnosis
    StartEngCareerDiagnosisUseCase,
    SubmitAnswersUseCase,
)
from app.config import get_settings
from app.domain.repositories import (
    StructuredDiagnosisRepository,
)
from app.infrastructure.llm import LLMService
from app.infrastructure.persistence import (
    FileStructuredDiagnosisRepository,
)


# LLM Service instance
@lru_cache
def get_llm_service() -> LLMServiceInterface:
    """Get the LLM service instance."""
    return LLMService()


# =============================================================================
# Engineer Career Diagnosis Dependencies
# =============================================================================


@lru_cache
def get_structured_diagnosis_repository() -> StructuredDiagnosisRepository:
    """Get the structured diagnosis repository instance."""
    settings = get_settings()
    return FileStructuredDiagnosisRepository(
        base_path=settings.sessions_dir / "eng_career_diagnosis"
    )


def get_eng_career_start_diagnosis_use_case() -> StartEngCareerDiagnosisUseCase:
    """Get the engineer career start diagnosis use case."""
    return StartEngCareerDiagnosisUseCase(
        repository=get_structured_diagnosis_repository(),
    )


def get_eng_career_select_domain_use_case() -> SelectDomainUseCase:
    """Get the engineer career select domain use case."""
    return SelectDomainUseCase(
        repository=get_structured_diagnosis_repository(),
    )


def get_eng_career_select_goal_use_case() -> SelectGoalUseCase:
    """Get the engineer career select goal use case."""
    return SelectGoalUseCase(
        repository=get_structured_diagnosis_repository(),
    )


def get_eng_career_submit_answers_use_case() -> SubmitAnswersUseCase:
    """Get the engineer career submit answers use case."""
    return SubmitAnswersUseCase(
        repository=get_structured_diagnosis_repository(),
        llm_service=get_llm_service(),
    )


def get_eng_career_get_roadmap_use_case() -> GetRoadmapUseCase:
    """Get the engineer career get roadmap use case."""
    return GetRoadmapUseCase(
        repository=get_structured_diagnosis_repository(),
    )
