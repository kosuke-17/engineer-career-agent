"""LangGraph state definitions for the roadmap generation workflow.

This module defines the state that flows through the LangGraph workflow,
carrying data between agents.
"""

from dataclasses import dataclass, field
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph.message import add_messages


@dataclass
class TechnologyContext:
    """Context data for a single technology from research.

    Attributes:
        name: Technology name (e.g., "React").
        summary: Brief summary of the technology.
        links: List of reference URLs with titles.
    """

    name: str
    summary: str
    links: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "summary": self.summary,
            "links": self.links,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TechnologyContext":
        """Create from dictionary representation."""
        return cls(
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            links=data.get("links", []),
        )


class AgentState(TypedDict, total=False):
    """State that flows through the LangGraph workflow.

    This state is passed between agents and accumulates results.

    Attributes:
        user_input: The original user request text.
        tags: List of technology tags extracted by the orchestrator agent.
        context: List of technology context data from research agent.
        roadmap_json: The final roadmap JSON output from roadmap agent.
        error: Error message if any agent fails.
        messages: Conversation messages (for LangGraph message handling).
        current_agent: Name of the currently executing agent.
    """

    # Input from user
    user_input: str

    # Orchestrator agent output
    tags: list[str]

    # Research agent output
    context: list[dict[str, Any]]

    # Roadmap agent output
    roadmap_json: dict[str, Any]

    # Error handling
    error: Optional[str]

    # LangGraph messages (for streaming/tracing)
    messages: Annotated[list, add_messages]

    # Current agent tracking (for WebSocket progress updates)
    current_agent: str


def create_initial_state(user_input: str) -> AgentState:
    """Create an initial state with user input.

    Args:
        user_input: The user's roadmap generation request.

    Returns:
        Initial AgentState ready for the workflow.
    """
    return AgentState(
        user_input=user_input,
        tags=[],
        context=[],
        roadmap_json={},
        error=None,
        messages=[],
        current_agent="",
    )

