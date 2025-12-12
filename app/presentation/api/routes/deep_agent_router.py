from deepagents import create_deep_agent
from fastapi import APIRouter
from pydantic import BaseModel, field_validator
from tavily import TavilyClient

from app.config import get_settings
from app.infrastructure.llm.factory import get_llm


class DeepAgentRequest(BaseModel):
    """Request model for deep agent."""

    user_input: str

    @field_validator("user_input")
    @classmethod
    def validate_user_input(cls, v: str) -> str:
        """Validate that user_input is not empty."""
        if not v or not v.strip():
            raise ValueError("ユーザー入力は必須です")
        return v.strip()


router = APIRouter()

settings = get_settings()
tavily_client = TavilyClient(api_key=settings.tavily_api_key)

# LLMインスタンスを取得
llm = get_llm()


def internet_search(query: str, max_results: int = 5):
    """Run a web search"""
    return tavily_client.search(query, max_results=max_results)


agent = create_deep_agent(
    model=llm,
    tools=[internet_search],
    # 日本語
    system_prompt="日本語で研究を行い、洗練されたレポートを作成してください。",
)


@router.post("/deep-agent")
async def deep_agent(request: DeepAgentRequest):
    print(request.user_input)
    result = agent.invoke({"messages": [{"role": "user", "content": request.user_input}]})
    return {"message": result}
