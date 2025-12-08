"""Use case for streaming roadmap generation."""

from typing import Any, AsyncGenerator

from app.infrastructure.agents.roadmap_agent import roadmap_agent_stream
from app.infrastructure.agents.state import AgentState


class GenerateRoadmapStreamUseCase:
    """Use case for streaming roadmap generation."""

    async def execute(self, state: AgentState) -> AsyncGenerator[dict[str, Any], None]:
        """Execute the streaming roadmap generation use case.

        Args:
            state: Agent state containing user_input, tags, context, and sub_tags.

        Yields:
            Dictionary events with type:
                - "phase": Completed phase data
                - "complete": Final roadmap completion
                - "error": Error event

        Raises:
            ValueError: If required state fields are missing.
        """
        if not state.get("context"):
            yield {
                "type": "error",
                "error": "コンテキストが空です。先に/analyzeエンドポイントを呼び出してください。",
            }
            return

        if not state.get("tags"):
            yield {
                "type": "error",
                "error": "タグが空です。",
            }
            return

        async for event in roadmap_agent_stream(state):
            yield event
