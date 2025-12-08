"""Use case for generating a learning roadmap."""

from typing import Any

from app.infrastructure.agents.roadmap_agent import roadmap_agent
from app.infrastructure.agents.state import AgentState


class GenerateRoadmapUseCase:
    """Use case for generating a learning roadmap."""

    async def execute(self, state: AgentState) -> dict[str, Any]:
        """Execute the roadmap generation use case.

        Args:
            state: Agent state containing user_input, tags, context, and sub_tags.

        Returns:
            Dictionary containing:
                - roadmap: Generated roadmap JSON
                - error: Error message if generation fails

        Raises:
            ValueError: If required state fields are missing.
        """
        if not state.get("user_input"):
            raise ValueError("ユーザー入力は必須です")

        if not state.get("tags"):
            raise ValueError("タグリストは必須です")

        if not state.get("context"):
            raise ValueError("コンテキストは必須です")

        result = await roadmap_agent(state)

        if result.get("error"):
            return {
                "roadmap": {},
                "error": result.get("error"),
            }

        roadmap = result.get("roadmap_json", {})
        if not roadmap:
            return {
                "roadmap": {},
                "error": "Failed to generate roadmap",
            }

        return {
            "roadmap": roadmap,
            "error": result.get("error"),
        }
