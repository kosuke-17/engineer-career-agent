"""LLM service implementation."""

from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.application.services.llm_service import LLMServiceInterface
from app.domain.entities import DiagnosisSession
from app.domain.value_objects import Phase

from .factory import get_llm


class LLMService(LLMServiceInterface):
    """LLM service implementation using LangChain."""

    def __init__(self):
        self.llm = get_llm()

    async def generate_initial_message(
        self, session: DiagnosisSession
    ) -> str:
        """Generate the initial message for a diagnosis session."""
        system_prompt = self._get_system_prompt(session.current_phase)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="診断を開始してください。"),
        ]

        response = await self.llm.ainvoke(messages)
        return str(response.content)

    async def process_message(
        self, session: DiagnosisSession, user_message: str
    ) -> tuple[str, bool]:
        """Process a user message and generate a response."""
        system_prompt = self._get_system_prompt(session.current_phase)

        # Build message history
        messages = [SystemMessage(content=system_prompt)]

        for msg in session.messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg.content))

        # Add the new user message
        messages.append(HumanMessage(content=user_message))

        response = await self.llm.ainvoke(messages)
        response_text = str(response.content)

        # Check if phase should advance
        should_advance = self._should_advance_phase(response_text, session)

        return response_text, should_advance

    async def get_phase_result(
        self, session: DiagnosisSession
    ) -> Optional[dict[str, Any]]:
        """Get the result of the current phase."""
        # Build analysis prompt
        analysis_prompt = self._get_analysis_prompt(session.current_phase)

        conversation_text = "\n".join(
            f"{msg.role}: {msg.content}" for msg in session.messages
        )

        messages = [
            SystemMessage(content=analysis_prompt),
            HumanMessage(
                content=f"以下の会話から{session.current_phase.display_name}の結果を抽出してJSON形式で返してください:\n\n{conversation_text}"
            ),
        ]

        response = await self.llm.ainvoke(messages)

        # Try to parse JSON from response
        import json
        import re

        response_text = str(response.content)

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
            # Return a basic structure if parsing fails
            return {
                "phase": session.current_phase.value,
                "raw_response": response_text,
            }

    async def generate_roadmap(
        self,
        session: DiagnosisSession,
        skill_scores: list[dict[str, Any]],
        domain_aptitudes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate a learning roadmap based on diagnosis results."""
        roadmap_prompt = """あなたは学習ロードマップ生成の専門家です。
診断結果に基づいて、1年間の学習ロードマップを生成してください。

ロードマップは以下の形式でJSON形式で返してください:
{
    "target_role": "目標とする役職",
    "duration_months": 12,
    "quarters": [
        {
            "quarter": 1,
            "theme": "四半期のテーマ",
            "goals": ["目標1", "目標2"],
            "milestones": [
                {
                    "title": "マイルストーン名",
                    "description": "説明",
                    "skills": ["スキル1", "スキル2"],
                    "resources": [
                        {
                            "title": "リソース名",
                            "type": "course/book/project",
                            "url": "https://...",
                            "estimated_hours": 20
                        }
                    ],
                    "estimated_weeks": 4
                }
            ]
        }
    ],
    "prerequisites": ["前提知識1", "前提知識2"],
    "final_project": "最終プロジェクトの説明"
}"""

        skill_summary = "\n".join(
            f"- {s.get('name', 'unknown')}: {s.get('score', 0)}/10 ({s.get('level', 'unknown')})"
            for s in skill_scores
        )

        domain_summary = "\n".join(
            f"- {a.get('domain', 'unknown')}: {a.get('score', 0)}/10"
            for a in domain_aptitudes
        )

        messages = [
            SystemMessage(content=roadmap_prompt),
            HumanMessage(
                content=f"""以下の診断結果に基づいてロードマップを生成してください:

## スキルスコア
{skill_summary}

## 領域適性
{domain_summary}

JSON形式でロードマップを返してください。"""
            ),
        ]

        response = await self.llm.ainvoke(messages)

        # Parse JSON from response
        import json
        import re

        response_text = str(response.content)

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse roadmap",
                "raw_response": response_text,
            }

    def _get_system_prompt(self, phase: Phase) -> str:
        """Get the system prompt for a phase."""
        prompts = {
            Phase.FOUNDATION: """あなたはエンジニアのスキル診断を行う専門家です。
現在は「基礎スキル診断」フェーズです。

以下の項目について対話形式で評価してください:
- プログラミング基礎（変数、関数、制御構文）
- データ構造（配列、リスト、辞書、ツリー）
- アルゴリズム基礎（ソート、検索、計算量）
- バージョン管理（Git）
- 基本的な問題解決能力

質問は1-2個ずつ行い、回答に基づいて次の質問を調整してください。
10段階でスキルを評価してください。
十分な情報が集まったら、「基礎スキルの診断が完了しました」と伝えてください。""",
            Phase.DOMAIN: """あなたはエンジニアのキャリア診断を行う専門家です。
現在は「専攻領域選定」フェーズです。

以下の領域への適性を判定してください:
- フロントエンド開発
- バックエンド開発
- フルスタック開発
- DevOps/インフラ
- 機械学習エンジニアリング
- モバイル開発
- システムプログラミング

興味、経験、目標について質問し、最も適した領域を提案してください。
十分な情報が集まったら、「領域適性の診断が完了しました」と伝えてください。""",
            Phase.TECHNICAL: """あなたはエンジニアの技術スキル診断を行う専門家です。
現在は「詳細技術診断」フェーズです。

選定された領域に関する具体的な技術スキルを評価してください。
フレームワーク、ツール、設計パターンなどの知識と経験を確認してください。
十分な情報が集まったら、「技術診断が完了しました」と伝えてください。""",
            Phase.ARCHITECTURE: """あなたはソフトウェアアーキテクチャの専門家です。
現在は「アーキテクチャ適性」フェーズです。

システム設計能力を評価してください:
- スケーラビリティの考慮
- セキュリティ設計
- データモデリング
- マイクロサービス vs モノリス
- パフォーマンス最適化

十分な情報が集まったら、「アーキテクチャ診断が完了しました」と伝えてください。""",
            Phase.ROADMAP: """あなたは学習ロードマップの専門家です。
現在は「学習ロードマップ生成」フェーズです。

これまでの診断結果を踏まえて、最適な学習パスを提案してください。
具体的なリソース（書籍、コース、プロジェクト）を含めてください。""",
        }
        return prompts.get(phase, "診断を進めてください。")

    def _get_analysis_prompt(self, phase: Phase) -> str:
        """Get the analysis prompt for extracting phase results."""
        return f"""あなたは{phase.display_name}の結果を分析する専門家です。
会話から得られた情報を構造化してJSON形式で返してください。

以下の形式を使用してください:
{{
    "phase": "{phase.value}",
    "skills": [
        {{"name": "スキル名", "score": 7.5, "notes": "コメント"}}
    ],
    "aptitudes": [
        {{"domain": "領域名", "score": 8.0, "reasoning": "理由"}}
    ],
    "summary": "全体的なまとめ"
}}"""

    def _should_advance_phase(
        self, response: str, session: DiagnosisSession
    ) -> bool:
        """Check if the phase should advance based on the response."""
        completion_phrases = [
            "診断が完了しました",
            "診断を完了しました",
            "完了です",
            "次のフェーズ",
            "次に進みましょう",
        ]
        return any(phrase in response for phrase in completion_phrases)

