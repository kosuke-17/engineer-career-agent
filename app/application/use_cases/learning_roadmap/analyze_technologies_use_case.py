"""Use case for analyzing technologies (orchestrator + research)."""

from typing import Any

from app.infrastructure.agents.orchestrator_agent import orchestrator_agent
from app.infrastructure.agents.research_agent import research_agent
from app.infrastructure.agents.state import AgentState, create_initial_state


class AnalyzeTechnologiesUseCase:
    """Use case for extracting tags and researching technologies."""

    async def execute(self, user_input: str) -> dict[str, Any]:
        """Execute the analyze use case.

        This combines orchestrator and research agents:
        1. Extracts technology tags from user input
        2. Researches each technology using Tavily

        Args:
            user_input: The user's input text.

        Returns:
            Dictionary containing:
                - tags: List of extracted technology tags
                - sub_tags: List of sub-tags (keywords) for technologies
                - context: List of technology context data from research
                - error: Error message if any step fails

        Raises:
            ValueError: If user_input is empty or invalid.
        """
        if not user_input or not user_input.strip():
            raise ValueError("ユーザー入力は必須です")

        # Step 1: Extract tags using orchestrator
        state = create_initial_state(user_input.strip())
        orchestrator_result = await orchestrator_agent(state)

        if orchestrator_result.get("error"):
            return {
                "tags": [],
                "sub_tags": [],
                "context": [],
                "error": f"Orchestrator error: {orchestrator_result.get('error')}",
            }

        tags = orchestrator_result.get("tags", [])
        if not tags:
            return {
                "tags": [],
                "sub_tags": [],
                "context": [],
                "error": "No tags extracted from user input",
            }

        # Step 2: Research technologies using research agent
        research_state: AgentState = {
            "user_input": user_input.strip(),
            "tags": tags,
            "context": [],
            "roadmap_json": {},
            "error": None,
            "messages": [],
            "current_agent": "",
        }

        research_result = await research_agent(research_state)

        if research_result.get("error"):
            return {
                "tags": tags,
                "sub_tags": orchestrator_result.get("sub_tags", []),
                "context": [],
                "error": f"Research error: {research_result.get('error')}",
            }

        return {
            "tags": tags,
            "sub_tags": orchestrator_result.get("sub_tags", []),
            "context": research_result.get("context", []),
            "error": research_result.get("error"),
        }
