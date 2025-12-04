"""Learning Roadmap API router with HTTP streaming support.

This router provides endpoints for generating learning roadmaps
using the LangGraph agent workflow.
"""

import json
from typing import Any, AsyncIterator, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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


async def _generate_stream(user_request: str) -> AsyncIterator[str]:
    """Generate streaming response for roadmap generation.

    Yields JSON lines (ndjson) format for each agent progress.

    Args:
        user_request: The user's roadmap request.

    Yields:
        JSON string for each progress event, followed by newline.
    """
    use_case = GenerateRoadmapUseCase()
    dto_request = GenerateRoadmapRequest(user_request=user_request)

    try:
        async for event in use_case.execute_streaming(dto_request):
            chunk = {
                "type": event.event_type,
                "agent": event.agent,
                "data": event.data,
            }
            yield json.dumps(chunk, ensure_ascii=False) + "\n"

    except Exception as e:
        error_chunk = {
            "type": "error",
            "agent": "system",
            "data": {"error": str(e)},
        }
        yield json.dumps(error_chunk, ensure_ascii=False) + "\n"


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

    Client usage (JavaScript):
    ```javascript
    const response = await fetch('/api/learning-roadmap/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({request: 'ReactとNext.jsの学習ロードマップを作成したい'})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        const lines = decoder.decode(value).split('\\n').filter(Boolean);
        for (const line of lines) {
            const event = JSON.parse(line);
            console.log(event.agent, event.data);
        }
    }
    ```

    Args:
        request: The generation request with user input.

    Returns:
        StreamingResponse with JSON Lines content.
    """
    if not request.request or not request.request.strip():
        # Return error as streaming response for consistency
        async def error_stream() -> AsyncIterator[str]:
            yield (
                json.dumps(
                    {
                        "type": "error",
                        "agent": "system",
                        "data": {"error": "Request text is required"},
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

        return StreamingResponse(
            error_stream(),
            media_type="application/x-ndjson",
        )

    return StreamingResponse(
        _generate_stream(request.request),
        media_type="application/x-ndjson",
    )
