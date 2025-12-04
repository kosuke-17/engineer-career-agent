"""Generate learning roadmap use case.

This use case orchestrates the LangGraph workflow for generating
a learning roadmap based on user input.
"""

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

from app.infrastructure.agents.graph import (
    stream_roadmap_workflow,
)


@dataclass
class GenerateRoadmapRequest:
    """Request DTO for generating a learning roadmap.

    Attributes:
        user_request: The user's natural language request describing
                     what technologies they want to learn.
    """

    user_request: str


@dataclass
class RoadmapProgressEvent:
    """Event emitted during roadmap generation for streaming.

    Attributes:
        agent: Name of the agent that produced this event.
        event_type: Type of event ('progress' or 'complete').
        data: Event data containing agent output.
        is_final: Whether this is the final event.
    """

    agent: str
    event_type: str  # 'progress' or 'complete'
    data: dict[str, Any]
    is_final: bool = False


@dataclass
class GenerateRoadmapResponse:
    """Response DTO for the generated roadmap.

    Attributes:
        success: Whether the generation was successful.
        roadmap: The generated roadmap JSON (if successful).
        extracted_tags: Technology tags extracted from the request.
        context: Technology context from research.
        error: Error message (if failed).
    """

    success: bool
    roadmap: Optional[dict[str, Any]] = None
    extracted_tags: list[str] = field(default_factory=list)
    context: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "roadmap": self.roadmap,
            "extractedTags": self.extracted_tags,
            "context": self.context,
            "error": self.error,
        }


class GenerateRoadmapUseCase:
    """Use case for generating a learning roadmap.

    This use case executes the LangGraph workflow that:
    1. Extracts technology tags from user input (Orchestrator Agent)
    2. Researches each technology using Tavily (Research Agent)
    3. Generates a structured roadmap in JSON (Roadmap Agent)
    """

    async def execute_streaming(
        self,
        request: GenerateRoadmapRequest,
    ) -> AsyncIterator[RoadmapProgressEvent]:
        """Execute the roadmap generation workflow with streaming.

        This method yields progress events as each agent completes,
        suitable for WebSocket streaming.

        Args:
            request: The generation request with user input.

        Yields:
            RoadmapProgressEvent for each agent completion.
        """
        if not request.user_request or not request.user_request.strip():
            yield RoadmapProgressEvent(
                agent="system",
                event_type="error",
                data={"error": "User request is required"},
                is_final=True,
            )
            return

        try:
            async for event in stream_roadmap_workflow(request.user_request):
                agent_name = event.get("agent", "unknown")
                state = event.get("state", {})
                is_final = event.get("is_final", False)

                # Determine event type
                event_type = "complete" if is_final else "progress"

                # Extract relevant data based on agent
                if agent_name == "orchestrator":
                    data = {
                        "tags": state.get("tags", []),
                        "error": state.get("error"),
                    }
                elif agent_name == "research":
                    data = {
                        "context": state.get("context", []),
                        "error": state.get("error"),
                    }
                elif agent_name == "roadmap":
                    data = {
                        "roadmap": state.get("roadmap_json", {}),
                        "error": state.get("error"),
                    }
                else:
                    data = state

                yield RoadmapProgressEvent(
                    agent=agent_name,
                    event_type=event_type,
                    data=data,
                    is_final=is_final,
                )

        except Exception as e:
            yield RoadmapProgressEvent(
                agent="system",
                event_type="error",
                data={"error": f"Streaming error: {str(e)}"},
                is_final=True,
            )
