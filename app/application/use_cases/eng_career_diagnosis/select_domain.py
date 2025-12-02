"""Select domain use case."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.constants import Domain, get_goals_for_domain
from app.domain.repositories import StructuredDiagnosisRepository


@dataclass
class SelectDomainRequest:
    """Request to select a domain."""

    session_id: str
    domain: str


@dataclass
class SelectDomainResponse:
    """Response after selecting a domain."""

    session_id: str
    message: str
    current_phase: str
    selected_domain: str
    goals: list[dict[str, Any]] = field(default_factory=list)


class SelectDomainUseCase:
    """Use case for selecting a domain."""

    def __init__(self, repository: StructuredDiagnosisRepository):
        self.repository = repository

    async def execute(self, request: SelectDomainRequest) -> SelectDomainResponse:
        """Execute the use case.

        Args:
            request: The select domain request.

        Returns:
            SelectDomainResponse with goal options.

        Raises:
            ValueError: If session not found or invalid domain.
        """
        # Find the session
        session = await self.repository.find_by_id(request.session_id)
        if not session:
            raise ValueError(f"Session not found: {request.session_id}")

        # Validate domain
        valid_domains = [d.value for d in Domain]
        if request.domain not in valid_domains:
            raise ValueError(f"Invalid domain: {request.domain}. Must be one of: {valid_domains}")

        # Select domain
        session.select_domain(request.domain)

        # Save the session
        await self.repository.save(session)

        # Get goals for the selected domain
        goals = get_goals_for_domain(request.domain)
        goals_data = [goal.to_dict() for goal in goals]

        # Get domain display name
        domain_display = Domain(request.domain).display_name

        return SelectDomainResponse(
            session_id=session.id,
            message=f"{domain_display}を選択しました。次に、学習のゴールを選択してください。",
            current_phase=session.current_phase.value,
            selected_domain=request.domain,
            goals=goals_data,
        )
