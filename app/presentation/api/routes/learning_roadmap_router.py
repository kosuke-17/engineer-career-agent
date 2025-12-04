"""Learning Roadmap API router with HTTP streaming support.

This router provides endpoints for generating learning roadmaps
using the LangGraph agent workflow.
"""

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from app.application.use_cases.learning_roadmap import (
    GenerateRoadmapRequest,
    GenerateRoadmapUseCase,
)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


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


# =============================================================================
# Streaming API Endpoint
# =============================================================================


@router.post("/stream")
async def stream_roadmap(
    request: GenerateRoadmapRequestModel,
) -> StreamingResponse:
    """Generate a learning roadmap with streaming response.

    This endpoint streams progress updates as each agent completes.
    Response format is JSON Lines (ndjson) - one JSON object per line.

    Example response stream:
    ```
    {"type": "progress", "agent": "orchestrator", "data": {"tags": ["React", "Next.js"]}}
    {"type": "progress", "agent": "research", "data": {"context": [...]}}
    {"type": "complete", "agent": "roadmap", "data": {"roadmap": {...}}}
    ```

    Args:
        request: The generation request with user input.

    Returns:
        StreamingResponse with JSON Lines content.
    """
    use_case = GenerateRoadmapUseCase()
    dto_request = GenerateRoadmapRequest(user_request=request.request)

    return StreamingResponse(
        use_case.stream_ndjson(dto_request),
        media_type="application/x-ndjson",
    )
