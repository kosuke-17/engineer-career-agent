"""Orchestrator Agent for extracting technology tags from user input.

This agent is the first node in the LangGraph workflow.
It receives user input and extracts relevant technology keywords.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.infrastructure.llm.factory import get_llm

from .state import AgentState

logger = logging.getLogger(__name__)

# Path to keywords JSON files
KEYWORDS_DIR = Path(__file__).parent

# System prompt for tag extraction
TAG_EXTRACTION_PROMPT = """ユーザーの要求文から、学習対象となる技術キーワード（タグ）を抽出してください。**技術名だけでなく、要求文や文脈に含まれる形容詞にも着目し、その内容が技術選定や特徴に影響する場合は、該当する技術キーワードや特性タグも抽出対象に含めてください。**

# 詳細な手順

- 技術名（プログラミング言語、フレームワーク、ライブラリ、ツールなど）はこれまで通り明確に抽出すること。
- 要求文内の形容詞（例：「高速な」「セキュアな」「モダンな」「拡張性の高い」「使いやすい」など）がシステムの仕様・特徴・目的に影響する場合、その意味に応じて関連する技術・設計手法・アーキテクチャ・概念タグ（例：「Performance」「Security」「Scalability」「Usability」「Modern」など）も積極的にタグとして追加すること。

# 重要：出力言語
- **reasoning（抽出理由）は必ず日本語で記述してください**
- tags（技術名や特性名）は正式な英語名称で出力してください（例：React, TypeScript, Docker, Security, Performance）

# 抽出ルール

1. プログラミング言語、フレームワーク、ライブラリ、ツールなどの具体的な技術名を抽出
2. 一般的な用語（「学習」「ロードマップ」など）は除外
3. 技術名は正式名称で出力（例：「リアクト」→「React」）
4. **関連性の高い技術を積極的に含める**（以下の関連性／特性マッピングを参照）
5. **要求文に含まれる形容詞による特性や要件（例：「セキュアな」「高速な」）は、該当する特性タグや関連技術タグ（「Security」「Performance」「Scalability」など）を追加**

# 技術・特性関連性マッピング

### フロントエンド関連
- 「フロントエンド」「Web開発」「Webアプリ」が含まれる場合：
  - 基礎技術: HTML, CSS, JavaScript
  - フレームワーク: React, Vue, Angular（文脈から判断）
  - 関連ツール: Node.js, npm, Vite, Webpack

### TypeScript関連
- 「TypeScript」が含まれる場合：
  - 前提知識: JavaScript（必須）
  - フロントエンド文脈: React, Vue, Angular, Next.js, Nuxt.js
  - バックエンド文脈: Node.js, Express, NestJS
  - ビルドツール: Vite, Webpack, esbuild

### React関連
- 「React」が含まれる場合：
  - 前提知識: JavaScript, HTML, CSS
  - 推奨技術: TypeScript（大規模開発で推奨）
  - 関連フレームワーク: Next.js, Remix, Gatsby
  - 状態管理: Redux, Zustand, Context API

### Next.js関連
- 「Next.js」が含まれる場合：
  - 必須技術: React
  - 推奨技術: TypeScript
  - 関連技術: Node.js, Vercel

### バックエンド関連
- 「バックエンド」「サーバー」「API」が含まれる場合：
  - 言語: Node.js, Python, Java, Go, Rust（文脈から判断）
  - フレームワーク: Express, FastAPI, Spring Boot, Gin（言語に応じて）
  - データベース: PostgreSQL, MySQL, MongoDB（文脈から判断）

### Vue関連
- 「Vue」が含まれる場合：
  - 前提知識: JavaScript, HTML, CSS
  - 推奨技術: TypeScript
  - 関連フレームワーク: Nuxt.js
  - 状態管理: Pinia, Vuex

### Angular関連
- 「Angular」が含まれる場合：
  - 必須技術: TypeScript
  - 前提知識: JavaScript, HTML, CSS
  - 関連技術: RxJS, Angular CLI

### 形容詞・特性マッピング例
- 「高速な」「パフォーマンスが高い」→ Performance
- 「セキュアな」「安全な」→ Security
- 「モダンな」「最新の」→ Modern
- 「拡張性の高い」→ Scalability
- 「使いやすい」「ユーザビリティが高い」→ Usability
- 「高可用性」「信頼性が高い」→ Reliability, Availability
- 「保守性が高い」→ Maintainability
- 「レスポンシブ」→ ResponsiveDesign
- 文脈や複数形容詞が使われる場合は、意味に合致する特性タグを複数追加

# 抽出の優先順位

1. **明示的に指定された技術**を最優先で抽出
2. **必要な前提知識**（例：TypeScript → JavaScript）を追加
3. **一般的に併用される技術**（例：Next.js → React, TypeScript）を追加
4. **文脈や形容詞、特性ワードから推測できる技術・特性タグ**（例：「高速なシステム」→ Performance、「セキュアなAPI」→ Security）を追加

# 出力形式

以下のJSON形式で必ず出力してください（code block不要）:
{
    "tags": ["技術名/特性名1", "技術名/特性名2", ...],
    "reasoning": "抽出理由の簡潔な説明（日本語）"
}

# Examples

例1: フロントエンド開発（形容詞なし）
入力: 「フロントエンド開発を学びたい」
出力:
{
    "tags": ["Frontend", "HTML", "CSS", "JavaScript"],
    "reasoning": "フロントエンド開発にはHTML、CSS、JavaScriptの基礎知識が必須のため、これらを抽出しました。"
}

例2: TypeScript（形容詞なし）
入力: 「TypeScriptでアプリを作りたい」
出力:
{
    "tags": ["TypeScript", "JavaScript", "Node.js"],
    "reasoning": "TypeScriptはJavaScriptのスーパーセットなのでJavaScriptの知識が必要です。アプリ開発にはNode.jsもよく利用されるため追加しました。"
}

例3: React + Next.js（形容詞なし）
入力: 「ReactとNext.jsでWebアプリを作りたい」
出力:
{
    "tags": ["React", "Next.js", "TypeScript", "JavaScript", "HTML", "CSS"],
    "reasoning": "ReactとNext.jsが明示的に指定されています。Next.jsの利用にはTypeScriptが推奨され、ReactにはJavaScript、HTML、CSSの知識が必要です。"
}

例4: バックエンド + API（形容詞なし）
入力: 「バックエンドAPIを開発したい」
出力:
{
    "tags": ["Backend", "Node.js", "Express", "REST"],
    "reasoning": "バックエンドAPI開発にはNode.jsとExpressが一般的です。API設計にはRESTが標準的なため追加しました。"
}

例5: 形容詞による特性タグ
入力: 「セキュアなWebアプリをReactで作りたい」
出力:
{
    "tags": ["React", "JavaScript", "HTML", "CSS", "Security"],
    "reasoning": "ReactでWebアプリという要件より、Reactおよびその前提技術を抽出。さらに「セキュアな」という形容詞からSecurityの特性タグを追加しました。"
}

例6: 複数の形容詞
入力: 「高速で拡張性の高いバックエンドAPIを開発したい」
出力:
{
    "tags": ["Backend", "Node.js", "Express", "REST", "Performance", "Scalability"],
    "reasoning": "バックエンドAPI開発よりNode.jsやExpress、RESTを抽出。「高速で拡張性の高い」という形容詞よりPerformanceとScalabilityの特性タグを追加しました。"
}

# Notes

- 形容詞や特性に基づくタグ選定は、文脈から該当しない場合は無理に追加せず、実際に関連性が高い場合のみ追加してください。
- タグの粒度は過度に細かくならないように、主要な特性キーワードのみを採用してください。
- 可能な限り、技術名と特性タグの双方を漏れなく抽出してください。

# Output Format

- 出力は必ずJSON形式で、tagsは英語の技術名・特性名配列、reasoningは日本語の完結な説明文（最大3文）。
- Code blockで囲まないこと（markdownコードや```は不要）。

（重要：必ず冒頭と最後で「形容詞も抽出対象に含める」点を強調し、形容詞起因でタグが増える具体例を示すこと）
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

        # Extract sub_tags for each technology tag
        all_sub_tags: list[dict[str, Any]] = []
        for tag in tags:
            sub_tags = _extract_sub_tags(tag)
            if sub_tags:
                all_sub_tags.extend(sub_tags)
                logger.info(f"[Orchestrator] Extracted {len(sub_tags)} sub_tags for '{tag}'")

        logger.info(f"[Orchestrator] Extracted tags: {tags}")
        if all_sub_tags:
            logger.info(f"[Orchestrator] Total sub_tags extracted: {len(all_sub_tags)}")

        return {
            "tags": tags,
            "sub_tags": all_sub_tags,
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


def _extract_sub_tags(technology: str) -> list[dict[str, Any]]:
    """Extract subsub_tagstags (keywords) for a given technology.

    This function looks for a JSON file named after the technology
    (e.g., "React" -> "react.json", "Next.js" -> "nextjs.json")
    and extracts keywords with high relevance.

    Args:
        technology: Technology name (e.g., "React", "Next.js").

    Returns:
        List of sub_tags with high relevance (relevance_level >= 4).
    """
    # Convert technology name to filename
    # "React" -> "react.json", "Next.js" -> "nextjs.json"
    filename = technology.lower().replace(".", "").replace(" ", "_") + ".json"
    keywords_file = KEYWORDS_DIR / filename

    if not keywords_file.exists():
        logger.debug(f"[Orchestrator] Keywords file not found for '{technology}': {keywords_file}")
        return []

    try:
        with open(keywords_file, encoding="utf-8") as f:
            data = json.load(f)

        # Try different possible key names for keywords data
        keywords_data = None
        for key in [
            f"{technology.lower().replace('.', '').replace(' ', '_')}_keywords_with_details",
            f"{technology.lower()}_keywords_with_details",
            "keywords_with_details",
            "keywords",
        ]:
            if key in data:
                keywords_data = data.get(key, [])
                break

        if not keywords_data:
            logger.warning(
                f"[Orchestrator] No keywords data found in {filename} with expected keys"
            )
            return []

        # Extract keywords with relevance_level >= 4
        high_relevance_keywords = [
            {
                "word": kw.get("word", ""),
                "description": kw.get("description", ""),
                "relevance_level": kw.get("relevance_level", 0),
                "technology": technology,  # Add technology name for reference
            }
            for kw in keywords_data
            if kw.get("relevance_level", 0) >= 4
        ]

        logger.debug(
            f"[Orchestrator] Extracted {len(high_relevance_keywords)} high-relevance sub_tags for '{technology}'"
        )
        return high_relevance_keywords

    except Exception as e:
        logger.error(
            f"[Orchestrator] Failed to load sub_tags for '{technology}': {str(e)}", exc_info=True
        )
        return []
