"""Orchestrator Agent for extracting technology tags from user input.

This agent is the first node in the LangGraph workflow.
It receives user input and extracts relevant technology keywords.
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.infrastructure.llm.factory import get_llm

from .state import AgentState

logger = logging.getLogger(__name__)

# System prompt for tag extraction
TAG_EXTRACTION_PROMPT = """あなたは技術タグ抽出の専門家です。
ユーザーの要求文から、学習対象となる技術キーワード（タグ）を抽出してください。

## 重要：出力言語
- **reasoning（抽出理由）は必ず日本語で記述してください**
- tags（技術名）は正式な英語名称で出力してください（例：React, TypeScript, Docker）

## 抽出ルール
1. プログラミング言語、フレームワーク、ライブラリ、ツールなどの具体的な技術名を抽出
2. 一般的な用語（「学習」「ロードマップ」など）は除外
3. 技術名は正式名称で出力（例：「リアクト」→「React」）
4. 関連性の高い技術も含める（例：Next.jsが含まれる場合、Reactも含める）

## 出力形式
必ず以下のJSON形式で出力してください：
```json
{
    "tags": ["技術名1", "技術名2", "技術名3"],
    "reasoning": "抽出理由の簡潔な説明（日本語で記述）"
}
```

## 例
入力: 「ReactとNext.jsでWebアプリを作りたい」
出力:
```json
{
    "tags": ["React", "Next.js", "TypeScript"],
    "reasoning": "ReactとNext.jsがユーザーにより明示的に指定されています。Next.jsではTypeScriptの使用が推奨されるため、関連技術として追加しました。"
}
```
"""


async def orchestrator_agent(state: AgentState) -> dict[str, Any]:
    """Extract technology tags from user input.

    This is the orchestrator agent node in the LangGraph workflow.
    It analyzes the user's request and extracts relevant technology keywords.

    Args:
        state: Current agent state with user_input.

    Returns:
        Dictionary with extracted tags to merge into state.
    """
    user_input = state.get("user_input", "")

    logger.info("[Orchestrator] Starting tag extraction")
    logger.debug(f"[Orchestrator] User input: {user_input[:100]}...")

    if not user_input:
        logger.warning("[Orchestrator] No user input provided")
        return {
            "tags": [],
            "error": "No user input provided",
            "current_agent": "orchestrator",
        }

    try:
        logger.info("[Orchestrator] Invoking LLM for tag extraction")
        llm = get_llm()

        messages = [
            SystemMessage(content=TAG_EXTRACTION_PROMPT),
            HumanMessage(
                content=f"以下のユーザー要求から技術タグを抽出してください：\n\n{user_input}"
            ),
        ]

        response = await llm.ainvoke(messages)
        response_text = str(response.content)

        logger.debug(f"[Orchestrator] LLM response: {response_text[:200]}...")

        # Parse JSON from response
        tags = _parse_tags_response(response_text)

        if not tags:
            logger.warning("[Orchestrator] Failed to extract tags from response")
            return {
                "tags": [],
                "error": "Failed to extract tags from user input",
                "current_agent": "orchestrator",
            }

        logger.info(f"[Orchestrator] Extracted tags: {tags}")
        return {
            "tags": tags,
            "error": None,
            "current_agent": "orchestrator",
        }

    except Exception as e:
        logger.error(f"[Orchestrator] Error: {str(e)}", exc_info=True)
        return {
            "tags": [],
            "error": f"Orchestrator agent error: {str(e)}",
            "current_agent": "orchestrator",
        }


def _parse_tags_response(response_text: str) -> list[str]:
    """Parse tags from LLM response.

    Args:
        response_text: Raw LLM response text.

    Returns:
        List of extracted technology tags.
    """
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return data.get("tags", [])
        except json.JSONDecodeError:
            pass

    # Try to parse the entire response as JSON
    try:
        data = json.loads(response_text)
        return data.get("tags", [])
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    json_obj_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_obj_match:
        try:
            data = json.loads(json_obj_match.group(0))
            return data.get("tags", [])
        except json.JSONDecodeError:
            pass

    return []
