"""Learning Roadmap Generation Agent.

This agent generates a structured learning roadmap in JSON format
based on the technology context gathered by the research agent.
"""

import json
import logging
import re
from typing import Any, AsyncGenerator

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

4. **サブタグ（重要キーワード）の活用**:
   - 提供されたサブタグ（技術の重要キーワード）を参考に、学習トピックを具体的に設定
   - サブタグの`relevance_level`が高いもの（5）は基礎フェーズで必ず含める
   - サブタグの`description`を参考に、各トピックの説明を充実させる
   - 例：Reactのサブタグに「Component」「Hooks」「State」がある場合、これらを基礎フェーズのトピックとして含める

5. **論理的な順序**: 依存関係を考慮した学習順序を設定

6. **わかりやすい日本語**: 技術用語は適切に使用しつつ、説明は初学者にもわかりやすい日本語で記述
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
    sub_tags = state.get("sub_tags", [])

    logger.info(f"[Roadmap] Starting roadmap generation for tags: {tags}")
    logger.debug(f"[Roadmap] Context contains {len(context)} technologies")
    if sub_tags:
        logger.debug(f"[Roadmap] Sub_tags available: {len(sub_tags)} items")

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

        messages = _build_roadmap_messages(user_input, tags, context, sub_tags)

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


def _build_roadmap_messages(
    user_input: str,
    tags: list[str],
    context: list[dict[str, Any]],
    sub_tags: list[dict[str, Any]],
) -> list[SystemMessage | HumanMessage]:
    """Build messages for roadmap generation.

    Args:
        user_input: User's input text.
        tags: List of technology tags.
        context: List of technology context dictionaries.
        sub_tags: List of sub_tag dictionaries.

    Returns:
        List of messages for LLM.
    """
    context_text = _format_context(context)
    sub_tags_text = _format_sub_tags(sub_tags, tags)

    return [
        SystemMessage(content=ROADMAP_GENERATION_PROMPT),
        HumanMessage(
            content=f"""以下の技術調査結果に基づいて、学習ロードマップを生成してください。

## ユーザーの要求
{user_input}

## 対象技術
{", ".join(tags)}

## 調査結果
{context_text}

{sub_tags_text}

上記の情報を元に、JSON形式でロードマップを生成してください。
特に、サブタグ（重要キーワード）を参考にして、具体的で実践的な学習トピックを設定してください。"""
        ),
    ]


def _format_sub_tags(sub_tags: list[dict[str, Any]], tags: list[str]) -> str:
    """Format sub_tags for the prompt.

    Args:
        sub_tags: List of sub_tag dictionaries with word, description, relevance_level, technology.
        tags: List of technology tags.

    Returns:
        Formatted string for inclusion in the prompt.
    """
    if not sub_tags:
        return ""

    tags_dict: dict[str, list[dict[str, Any]]] = {}
    for sub_tag in sub_tags:
        tech = sub_tag.get("technology", "Unknown")
        if tech not in tags_dict:
            tags_dict[tech] = []
        tags_dict[tech].append(sub_tag)

    parts = ["## 重要キーワード（サブタグ）"]

    for tag in tags:
        if tag in tags_dict:
            tech_sub_tags = tags_dict[tag]
            # Sort by relevance_level (descending)
            tech_sub_tags.sort(key=lambda x: x.get("relevance_level", 0), reverse=True)

            parts.append(f"\n### {tag}の重要キーワード")
            for sub_tag in tech_sub_tags:
                word = sub_tag.get("word", "")
                description = sub_tag.get("description", "")
                relevance = sub_tag.get("relevance_level", 0)
                parts.append(f"- **{word}** (重要度: {relevance}/5): {description}")

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


async def roadmap_agent_stream(state: AgentState) -> AsyncGenerator[dict[str, Any], None]:
    """Stream roadmap generation from LLM response.

    This function streams the roadmap generation process, yielding
    partial and complete roadmap data as it becomes available.

    Args:
        state: Current agent state with context from research agent.

    Yields:
        Dictionary with streaming event data:
        - {"type": "chunk", "content": "partial JSON string"}
        - {"type": "progress", "roadmap": {...}, "complete": false}
        - {"type": "complete", "roadmap": {...}, "complete": true}
        - {"type": "error", "error": "error message"}
    """
    context = state.get("context", [])
    user_input = state.get("user_input", "")
    tags = state.get("tags", [])
    sub_tags = state.get("sub_tags", [])

    logger.info(f"[Roadmap Stream] Starting streaming roadmap generation for tags: {tags}")
    logger.debug(f"[Roadmap Stream] Context contains {len(context)} technologies")
    if sub_tags:
        logger.debug(f"[Roadmap Stream] Sub_tags available: {len(sub_tags)} items")

    if not context:
        logger.warning("[Roadmap Stream] No technology context available")
        yield {
            "type": "error",
            "error": state.get("error") or "No technology context available",
        }
        return

    try:
        logger.info("[Roadmap Stream] Invoking LLM for streaming roadmap generation")
        llm = get_llm()

        messages = _build_roadmap_messages(user_input, tags, context, sub_tags)

        # Buffer to accumulate streaming chunks
        buffer = ""
        last_valid_json: dict[str, Any] = {}

        # Stream LLM response
        async for chunk in llm.astream(messages):
            if hasattr(chunk, "content"):
                content = str(chunk.content)
                buffer += content

                # Yield raw chunk for progress indication
                yield {
                    "type": "chunk",
                    "content": content,
                }

                # Try to parse partial JSON from buffer
                # Look for complete JSON objects in the buffer
                parsed_json = _try_parse_partial_json(buffer)
                if parsed_json and parsed_json != last_valid_json:
                    last_valid_json = parsed_json
                    yield {
                        "type": "progress",
                        "roadmap": parsed_json,
                        "complete": False,
                    }

        # After streaming is complete, try to parse final JSON
        logger.debug(f"[Roadmap Stream] Final buffer length: {len(buffer)} chars")
        final_roadmap = _parse_roadmap_response(buffer)

        if not final_roadmap:
            logger.warning("[Roadmap Stream] Failed to parse final roadmap JSON")
            yield {
                "type": "error",
                "error": "Failed to parse roadmap JSON from response",
            }
            return

        tech_count = len(final_roadmap.get("technologies", []))
        logger.info(
            f"[Roadmap Stream] Successfully generated roadmap with {tech_count} technologies"
        )

        # Yield final complete roadmap
        yield {
            "type": "complete",
            "roadmap": final_roadmap,
            "complete": True,
        }

    except Exception as e:
        logger.error(f"[Roadmap Stream] Error: {str(e)}", exc_info=True)
        yield {
            "type": "error",
            "error": f"Roadmap agent error: {str(e)}",
        }


def _try_parse_partial_json(text: str) -> dict[str, Any]:
    """Try to parse partial JSON from streaming text.

    This function attempts to extract a valid JSON object from
    potentially incomplete text by finding the last complete JSON object.

    Args:
        text: Potentially incomplete JSON text.

    Returns:
        Parsed JSON dictionary if successful, empty dict otherwise.
    """
    # Try to find the last complete JSON object
    # Look for opening and closing braces
    brace_count = 0
    start_idx = -1

    for i, char in enumerate(text):
        if char == "{":
            if start_idx == -1:
                start_idx = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                # Found a complete JSON object
                try:
                    json_str = text[start_idx : i + 1]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Continue searching
                    pass

    # If no complete object found, try parsing the entire text
    # (might work if it's complete)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    return {}
