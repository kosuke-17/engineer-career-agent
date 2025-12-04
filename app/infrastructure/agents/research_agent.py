"""Technical Research Agent for gathering technology information using Tavily.

This agent searches for information about each technology tag
and compiles summaries and reference links.
"""

import asyncio
import logging
from typing import Any

from tavily import AsyncTavilyClient

from app.config import get_settings

from .state import AgentState, TechnologyContext

logger = logging.getLogger(__name__)


async def research_agent(state: AgentState) -> dict[str, Any]:
    """Research each technology tag using Tavily search.

    This agent queries Tavily for each technology tag and compiles
    summaries and reference links into a context structure.

    Args:
        state: Current agent state with tags from orchestrator.

    Returns:
        Dictionary with context data to merge into state.
    """
    tags = state.get("tags", [])

    logger.info(f"[Research] Starting research for tags: {tags}")

    if not tags:
        logger.warning("[Research] No tags to research")
        return {
            "context": [],
            "error": state.get("error") or "No tags to research",
            "current_agent": "research",
        }

    settings = get_settings()
    tavily_api_key = settings.tavily_api_key

    if not tavily_api_key:
        logger.error("[Research] Tavily API key not configured")
        return {
            "context": [],
            "error": "Tavily API key not configured",
            "current_agent": "research",
        }

    try:
        logger.info("[Research] Initializing Tavily client")
        client = AsyncTavilyClient(api_key=tavily_api_key)

        # Research all tags concurrently
        logger.info(f"[Research] Researching {len(tags)} technologies concurrently")
        research_tasks = [_research_technology(client, tag) for tag in tags]
        results = await asyncio.gather(*research_tasks, return_exceptions=True)

        context_list: list[dict[str, Any]] = []

        for tag, result in zip(tags, results):
            if isinstance(result, Exception):
                # If a specific tag fails, add it with error info
                logger.warning(f"[Research] Failed to research '{tag}': {str(result)}")
                context_list.append(
                    TechnologyContext(
                        name=tag,
                        summary=f"Research failed: {str(result)}",
                        links=[],
                    ).to_dict()
                )
            else:
                logger.info(
                    f"[Research] Successfully researched '{tag}' - {len(result.links)} links found"
                )
                context_list.append(result.to_dict())

        logger.info(f"[Research] Completed research for {len(context_list)} technologies")
        return {
            "context": context_list,
            "error": None,
            "current_agent": "research",
        }

    except Exception as e:
        logger.error(f"[Research] Error: {str(e)}", exc_info=True)
        return {
            "context": [],
            "error": f"Research agent error: {str(e)}",
            "current_agent": "research",
        }


async def _research_technology(
    client: AsyncTavilyClient,
    tag: str,
) -> TechnologyContext:
    """Research a single technology using Tavily.

    Args:
        client: Tavily async client instance.
        tag: Technology name to research.

    Returns:
        TechnologyContext with research results.
    """
    # Construct search query in Japanese for Japanese learning resources
    # Include Qiita, Zenn, and official documentation keywords for better Japanese results
    query = f"{tag} Qiita Zenn 公式ドキュメント"

    logger.debug(f"[Research] Searching for: {query}")

    # Search using Tavily with Japanese preference
    response = await client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
    )

    logger.debug(
        f"[Research] Tavily returned {len(response.get('results', []))} results for '{tag}'"
    )

    # Extract summary from Tavily's answer or construct from results
    summary = response.get("answer", "")
    if not summary and response.get("results"):
        # Fallback: Use content from top results
        summaries = [result.get("content", "")[:200] for result in response.get("results", [])[:3]]
        summary = " ".join(summaries)

    # Extract reference links
    links: list[dict[str, str]] = []
    for result in response.get("results", [])[:5]:
        title = result.get("title", "")
        url = result.get("url", "")
        if title and url:
            links.append({"title": title, "url": url})

    return TechnologyContext(
        name=tag,
        summary=summary or f"{tag}に関するプログラミング技術の情報です。",
        links=links,
    )
