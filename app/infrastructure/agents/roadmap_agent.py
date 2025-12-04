"""Learning Roadmap Generation Agent.

This agent generates a structured learning roadmap in JSON format
based on the technology context gathered by the research agent.
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.infrastructure.llm.factory import get_llm

from .state import AgentState

logger = logging.getLogger(__name__)

# System prompt for roadmap generation
ROADMAP_GENERATION_PROMPT = """あなたは学習ロードマップ生成の専門家です。
技術調査の結果に基づいて、構造化された学習ロードマップをJSON形式で生成してください。

## 重要：出力言語
**すべてのテキストは日本語で記述してください。**
- roadmapTitle: 日本語（例：「React・Next.js 学習ロードマップ」）
- summary: 日本語で技術の概要を説明
- phaseName: 日本語（例：「基礎」「応用」「実践」）
- topic: 日本語（例：「開発環境の構築」「コンポーネント設計」）
- title（リンクタイトル）: 元のタイトルを使用（英語の場合はそのまま）

## 出力形式
必ず以下のJSON形式で出力してください：

```json
{
  "roadmapTitle": "React・Next.js 学習ロードマップ",
  "technologies": [
    {
      "name": "React",
      "summary": "Reactは、Facebookが開発したUIライブラリです。コンポーネントベースの設計により、再利用可能なUI部品を構築できます。",
      "phases": [
        {
          "phaseName": "基礎",
          "order": 1,
          "steps": [
            {
              "topic": "開発環境の構築",
              "estimatedTime": "2時間",
              "sourceLinks": [
                {"title": "React公式ドキュメント", "url": "https://react.dev"}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## ロードマップ作成のガイドライン

1. **フェーズ構成**: 各技術について以下の3フェーズを設定
   - 基礎（order: 1）: 開発環境構築、基本概念の理解、初歩的な実装
   - 応用（order: 2）: 実践的なパターン、ベストプラクティス、高度な機能
   - 実践（order: 3）: プロジェクト制作、応用課題、ポートフォリオ作成

2. **学習時間の目安**（日本語で記述）:
   - 基礎トピック: 「2時間」「4時間」
   - 応用トピック: 「4時間」「8時間」
   - 実践トピック: 「8時間」「16時間」

3. **参考リンク**: 調査結果から提供されたリンクを活用

4. **論理的な順序**: 依存関係を考慮した学習順序を設定

5. **わかりやすい日本語**: 技術用語は適切に使用しつつ、説明は初学者にもわかりやすい日本語で記述
"""


async def roadmap_agent(state: AgentState) -> dict[str, Any]:
    """Generate a learning roadmap from technology context.

    This agent takes the research context and generates a structured
    learning roadmap in JSON format.

    Args:
        state: Current agent state with context from research agent.

    Returns:
        Dictionary with roadmap_json to merge into state.
    """
    context = state.get("context", [])
    user_input = state.get("user_input", "")
    tags = state.get("tags", [])

    logger.info(f"[Roadmap] Starting roadmap generation for tags: {tags}")
    logger.debug(f"[Roadmap] Context contains {len(context)} technologies")

    if not context:
        logger.warning("[Roadmap] No technology context available")
        return {
            "roadmap_json": {},
            "error": state.get("error") or "No technology context available",
            "current_agent": "roadmap",
        }

    try:
        logger.info("[Roadmap] Invoking LLM for roadmap generation")
        llm = get_llm()

        # Format context for the prompt
        context_text = _format_context(context)

        messages = [
            SystemMessage(content=ROADMAP_GENERATION_PROMPT),
            HumanMessage(
                content=f"""以下の技術調査結果に基づいて、学習ロードマップを生成してください。

## ユーザーの要求
{user_input}

## 対象技術
{", ".join(tags)}

## 調査結果
{context_text}

上記の情報を元に、JSON形式でロードマップを生成してください。"""
            ),
        ]

        response = await llm.ainvoke(messages)
        response_text = str(response.content)

        logger.debug(f"[Roadmap] LLM response length: {len(response_text)} chars")

        # Parse JSON from response
        roadmap_json = _parse_roadmap_response(response_text)

        if not roadmap_json:
            logger.warning("[Roadmap] Failed to parse roadmap JSON from response")
            return {
                "roadmap_json": {},
                "error": "Failed to parse roadmap JSON",
                "current_agent": "roadmap",
            }

        # Add metadata
        roadmap_json["userRequest"] = user_input
        roadmap_json["extractedTags"] = tags

        tech_count = len(roadmap_json.get("technologies", []))
        logger.info(f"[Roadmap] Successfully generated roadmap with {tech_count} technologies")
        return {
            "roadmap_json": roadmap_json,
            "error": None,
            "current_agent": "roadmap",
        }

    except Exception as e:
        logger.error(f"[Roadmap] Error: {str(e)}", exc_info=True)
        return {
            "roadmap_json": {},
            "error": f"Roadmap agent error: {str(e)}",
            "current_agent": "roadmap",
        }


def _format_context(context: list[dict[str, Any]]) -> str:
    """Format technology context for the prompt.

    Args:
        context: List of technology context dictionaries.

    Returns:
        Formatted string for inclusion in the prompt.
    """
    parts = []

    for tech in context:
        name = tech.get("name", "Unknown")
        summary = tech.get("summary", "No summary available")
        links = tech.get("links", [])

        link_text = "\n".join(
            f"  - {link.get('title', 'Link')}: {link.get('url', '')}" for link in links[:5]
        )

        parts.append(
            f"""### {name}
**要約**: {summary}

**参考リンク**:
{link_text if link_text else "  - なし"}
"""
        )

    return "\n".join(parts)


def _parse_roadmap_response(response_text: str) -> dict[str, Any]:
    """Parse roadmap JSON from LLM response.

    Args:
        response_text: Raw LLM response text.

    Returns:
        Parsed roadmap dictionary, or empty dict if parsing fails.
    """
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to parse the entire response as JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    json_obj_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_obj_match:
        try:
            return json.loads(json_obj_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
