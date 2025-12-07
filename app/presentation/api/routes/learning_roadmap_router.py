"""Learning Roadmap API router with HTTP streaming support.

This router provides endpoints for generating learning roadmaps
using the LangGraph agent workflow, as well as individual agent endpoints.
"""

import json
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.infrastructure.agents.orchestrator_agent import orchestrator_agent
from app.infrastructure.agents.research_agent import research_agent
from app.infrastructure.agents.roadmap_agent import roadmap_agent, roadmap_agent_stream
from app.infrastructure.agents.state import AgentState, create_initial_state
from app.presentation.api.dependencies import require_session

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class SubTag(BaseModel):
    description: str
    relevance_level: int
    technology: str
    word: str


class GenerateRoadmapRequestModel(BaseModel):
    """Request model for roadmap generation."""

    request: str

    @field_validator("request")
    @classmethod
    def validate_request(cls, v: str) -> str:
        """Validate that request is not empty."""
        if not v or not v.strip():
            raise ValueError("リクエストテキストは必須です")
        return v.strip()


class GenerateRoadmapResponseModel(BaseModel):
    """Response model for roadmap generation."""

    success: bool
    roadmap: Optional[dict[str, Any]] = None
    extracted_tags: list[str] = []
    context: list[dict[str, Any]] = []
    error: Optional[str] = None


# Orchestrator Agent Models
class OrchestratorRequestModel(BaseModel):
    """Request model for orchestrator agent."""

    user_input: str

    @field_validator("user_input")
    @classmethod
    def validate_user_input(cls, v: str) -> str:
        """Validate that user_input is not empty."""
        if not v or not v.strip():
            raise ValueError("ユーザー入力は必須です")
        return v.strip()


class OrchestratorResponseModel(BaseModel):
    """Response model for orchestrator agent."""

    tags: list[str]
    sub_tags: list[SubTag] = []
    error: Optional[str] = None


# Research Agent Models
class ResearchRequestModel(BaseModel):
    """Request model for research agent."""

    tags: list[str]

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate that tags is not empty."""
        if not v:
            raise ValueError("タグリストは必須です")
        return v


class ResearchResponse(BaseModel):
    """Response model for research agent."""

    context: list[dict[str, Any]]
    error: Optional[str] = None


# Roadmap Agent Models
class RoadmapRequest(BaseModel):
    """Request model for roadmap agent."""

    user_input: str
    tags: list[str]
    context: list[dict[str, Any]]
    sub_tags: list[SubTag] = []

    @field_validator("user_input")
    @classmethod
    def validate_user_input(cls, v: str) -> str:
        """Validate that user_input is not empty."""
        if not v or not v.strip():
            raise ValueError("ユーザー入力は必須です")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate that tags is not empty."""
        if not v:
            raise ValueError("タグリストは必須です")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate that context is not empty."""
        if not v:
            raise ValueError("コンテキストは必須です")
        return v


class RoadmapResponse(BaseModel):
    """Response model for roadmap agent."""

    roadmap: dict[str, Any]
    error: Optional[str] = None


# Analyze Request/Response Models (Orchestrator + Research)
class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint (orchestrator + research)."""

    user_input: str

    @field_validator("user_input")
    @classmethod
    def validate_user_input(cls, v: str) -> str:
        """Validate that user_input is not empty."""
        if not v or not v.strip():
            raise ValueError("ユーザー入力は必須です")
        return v.strip()


class AnalyzeResponse(BaseModel):
    """Response model for analyze endpoint.

    This response can be used directly to call the /roadmap endpoint.
    """

    user_input: str
    tags: list[str]
    sub_tags: list[SubTag] = []
    context: list[dict[str, Any]]
    error: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================


def _build_roadmap_state(request: RoadmapRequest) -> AgentState:
    """Build agent state from roadmap request.

    Args:
        request: The roadmap request with user input, tags, and context.

    Returns:
        AgentState dictionary for roadmap agent.
    """
    # Convert SubTag models to dicts for state
    sub_tags_dicts = [st.model_dump() for st in request.sub_tags]

    return {
        "user_input": request.user_input,
        "tags": request.tags,
        "sub_tags": sub_tags_dicts,
        "context": request.context,
        "roadmap_json": {},
        "error": None,
        "messages": [],
        "current_agent": "",
    }


# =============================================================================
# Individual Agent Endpoints
# =============================================================================
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_technologies(
    request: AnalyzeRequest, session: dict = Depends(require_session)
) -> AnalyzeResponse:
    """Extract tags and research technologies in one call.

    This endpoint combines orchestrator and research agents:
    1. Extracts technology tags from user input
    2. Researches each technology using Tavily

    Args:
        request: The analyze request with user input.

    Returns:
        AnalyzeResponseModel with extracted tags and research context.
    """
    # Step 1: Extract tags using orchestrator
    state = create_initial_state(request.user_input)
    orchestrator_result = await orchestrator_agent(state)

    if orchestrator_result.get("error"):
        raise HTTPException(
            status_code=500, detail=f"Orchestrator error: {orchestrator_result.get('error')}"
        )

    tags = orchestrator_result.get("tags", [])
    if not tags:
        raise HTTPException(status_code=500, detail="No tags extracted from user input")

    # Step 2: Research technologies using research agent
    research_state: AgentState = {
        "user_input": request.user_input,
        "tags": tags,
        "context": [],
        "roadmap_json": {},
        "error": None,
        "messages": [],
        "current_agent": "",
    }

    research_result = await research_agent(research_state)

    if research_result.get("error"):
        raise HTTPException(
            status_code=500, detail=f"Research error: {research_result.get('error')}"
        )

    # Convert sub_tags dicts to SubTag models
    sub_tags_raw = orchestrator_result.get("sub_tags", [])
    sub_tags_models = [SubTag(**st) for st in sub_tags_raw if isinstance(st, dict)]

    return AnalyzeResponse(
        user_input=request.user_input,
        tags=tags,
        sub_tags=sub_tags_models,
        context=research_result.get("context", []),
        error=research_result.get("error"),
    )


@router.post("/roadmap", response_model=RoadmapResponse)
async def generate_roadmap(
    request: RoadmapRequest, session: dict = Depends(require_session)
) -> RoadmapResponse:
    """Generate a learning roadmap from technology context.

    This endpoint uses the roadmap agent to generate a structured
    learning roadmap in JSON format.

    Args:
        request: The roadmap request with user input, tags, and context.

    Returns:
        RoadmapResponseModel with generated roadmap.
    """
    state = _build_roadmap_state(request)

    result = await roadmap_agent(state)

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result.get("error"))

    roadmap = result.get("roadmap_json", {})
    if not roadmap:
        raise HTTPException(status_code=500, detail="Failed to generate roadmap")

    return RoadmapResponse(
        roadmap=roadmap,
        error=result.get("error"),
    )


@router.post("/roadmap/stream")
async def generate_roadmap_stream(
    request: RoadmapRequest, session: dict = Depends(require_session)
) -> StreamingResponse:
    """Stream roadmap generation in JSON Lines format.

    This endpoint streams the roadmap generation process, yielding
    partial and complete roadmap data as it becomes available.

    Args:
        request: The roadmap request with user input, tags, and context.

    Returns:
        StreamingResponse with JSON Lines (ndjson) format.
    """
    state = _build_roadmap_state(request)

    async def stream_ndjson() -> AsyncGenerator[str, None]:
        """Generate JSON Lines from roadmap agent stream."""
        try:
            # Validate state before streaming
            if not state.get("context"):
                error_event = {
                    "type": "error",
                    "error": "コンテキストが空です。先に/analyzeエンドポイントを呼び出してください。",
                }
                yield f"{json.dumps(error_event, ensure_ascii=False)}\n"
                return

            if not state.get("tags"):
                error_event = {
                    "type": "error",
                    "error": "タグが空です。",
                }
                yield f"{json.dumps(error_event, ensure_ascii=False)}\n"
                return

            async for event in roadmap_agent_stream(state):
                # Convert event to JSON line
                try:
                    json_line = json.dumps(event, ensure_ascii=False)
                    yield f"{json_line}\n"
                except (TypeError, ValueError) as e:
                    # If JSON serialization fails, send error event
                    error_event = {
                        "type": "error",
                        "error": f"イベントのシリアライズに失敗しました: {str(e)}",
                    }
                    yield f"{json.dumps(error_event, ensure_ascii=False)}\n"
        except Exception as e:
            # Catch any unexpected errors during streaming
            error_event = {
                "type": "error",
                "error": f"ストリーミング中にエラーが発生しました: {str(e)}",
            }
            try:
                yield f"{json.dumps(error_event, ensure_ascii=False)}\n"
            except Exception:
                # If even error serialization fails, send plain text
                yield '{"type":"error","error":"ストリーミングエラー"}\n'

    return StreamingResponse(
        stream_ndjson(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
