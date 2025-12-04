"""LangGraph workflow for learning roadmap generation.

This module defines the workflow graph that connects the three agents:
1. Orchestrator Agent (tag extraction)
2. Research Agent (Tavily search)
3. Roadmap Agent (JSON generation)
"""

import logging
from typing import Any, AsyncIterator

from langgraph.graph import END, StateGraph

from .orchestrator_agent import orchestrator_agent
from .research_agent import research_agent
from .roadmap_agent import roadmap_agent
from .state import AgentState, create_initial_state

logger = logging.getLogger(__name__)


def create_roadmap_graph() -> StateGraph:
    """Create the LangGraph workflow for roadmap generation.

    The workflow follows this structure:
    START -> orchestrator -> research -> roadmap -> END

    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create the graph with AgentState
    workflow = StateGraph(AgentState)

    # Add nodes (agents)
    workflow.add_node("orchestrator", orchestrator_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("roadmap", roadmap_agent)

    # Define edges (flow)
    workflow.set_entry_point("orchestrator")
    workflow.add_edge("orchestrator", "research")
    workflow.add_edge("research", "roadmap")
    workflow.add_edge("roadmap", END)

    # Compile the graph
    return workflow.compile()


async def run_roadmap_workflow(user_input: str) -> dict[str, Any]:
    """Run the complete roadmap generation workflow.

    Args:
        user_input: User's roadmap generation request.

    Returns:
        Final state with roadmap_json or error.
    """
    logger.info("[Workflow] Starting roadmap generation workflow")
    logger.debug(f"[Workflow] User input: {user_input[:100]}...")

    graph = create_roadmap_graph()
    initial_state = create_initial_state(user_input)

    final_state = await graph.ainvoke(initial_state)

    if final_state.get("error"):
        logger.error(f"[Workflow] Completed with error: {final_state.get('error')}")
    else:
        logger.info("[Workflow] Completed successfully")

    return dict(final_state)


async def stream_roadmap_workflow(user_input: str) -> AsyncIterator[dict[str, Any]]:
    """Stream the roadmap generation workflow with progress updates.

    This generator yields updates after each agent completes,
    suitable for streaming response.

    Args:
        user_input: User's roadmap generation request.

    Yields:
        Progress updates with agent name and current state.
    """
    logger.info("[Workflow] Starting streaming roadmap generation")
    logger.debug(f"[Workflow] User input: {user_input[:100]}...")

    graph = create_roadmap_graph()
    initial_state = create_initial_state(user_input)

    # Stream events from the graph
    async for event in graph.astream(initial_state, stream_mode="updates"):
        # Each event contains the node name and its output
        for node_name, node_output in event.items():
            logger.info(f"[Workflow] Agent '{node_name}' completed")
            yield {
                "agent": node_name,
                "state": node_output,
                "is_final": node_name == "roadmap",
            }

    logger.info("[Workflow] Streaming workflow completed")
