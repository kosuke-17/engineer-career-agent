"""LLM service implementation."""

import json
import re
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.application.dto import Answer, Question, QuestionOption, StructuredResponse
from app.application.services.llm_service import LLMServiceInterface
from app.domain.entities import DiagnosisSession
from app.domain.value_objects import Phase

from .factory import get_llm


class LLMService(LLMServiceInterface):
    """LLM service implementation using LangChain."""

    def __init__(self):
        self.llm = get_llm()

    async def generate_initial_response(
        self, session: DiagnosisSession
    ) -> StructuredResponse:
        """Generate the initial response for a diagnosis session."""
        system_prompt = self._get_system_prompt(session.current_phase)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="診断を開始してください。"),
        ]

        response = await self.llm.ainvoke(messages)
        return self._parse_structured_response(str(response.content))

    async def process_answers(
        self,
        session: DiagnosisSession,
        answers: list[Answer],
        supplement: Optional[str],
    ) -> StructuredResponse:
        """Process user answers and generate a response."""
        system_prompt = self._get_system_prompt(session.current_phase)

        # Build message history
        messages = [SystemMessage(content=system_prompt)]

        for msg in session.messages:
            if msg.role == "user":
                # Format user's answers for context
                content = self._format_user_message(msg.content, msg.answers)
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=msg.content))

        # Format the new user answers
        user_content = self._format_answers(answers, supplement)
        messages.append(HumanMessage(content=user_content))

        response = await self.llm.ainvoke(messages)
        return self._parse_structured_response(str(response.content))

    async def get_phase_result(
        self, session: DiagnosisSession
    ) -> Optional[dict[str, Any]]:
        """Get the result of the current phase."""
        analysis_prompt = self._get_analysis_prompt(session.current_phase)

        # Build conversation summary including answers
        conversation_parts = []
        for msg in session.messages:
            if msg.role == "user" and msg.answers:
                formatted = self._format_user_message(msg.content, msg.answers)
                conversation_parts.append(f"user: {formatted}")
            else:
                conversation_parts.append(f"{msg.role}: {msg.content}")

        conversation_text = "\n".join(conversation_parts)

        messages = [
            SystemMessage(content=analysis_prompt),
            HumanMessage(
                content=f"以下の会話から{session.current_phase.display_name}の結果を抽出してJSON形式で返してください:\n\n{conversation_text}"
            ),
        ]

        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(str(response.content))

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
        result = self._parse_json_response(str(response.content))
        return result or {"error": "Failed to parse roadmap"}

    def _get_system_prompt(self, phase: Phase) -> str:
        """Get the system prompt for a phase with structured output format."""
        base_instruction = """
あなたの応答は必ず以下のJSON形式で返してください:
```json
{
    "message": "ユーザーへのメッセージ（説明やフィードバック）",
    "questions": [
        {
            "id": "q1",
            "text": "質問文",
            "type": "single" または "multiple",
            "options": [
                {"id": "opt1", "label": "選択肢1"},
                {"id": "opt2", "label": "選択肢2"}
            ]
        }
    ],
    "should_advance": false
}
```

- "message": ユーザーへの説明やコメント
- "questions": 選択式の質問リスト（1-3問程度）
- "type": "single"は単一選択、"multiple"は複数選択可
- "should_advance": このフェーズを完了して次に進むべき場合はtrue

質問は2-3問を1セットで出し、回答を受けたら次の質問セットを出してください。
2-3回の質問セットでフェーズを完了させてください。
"""

        prompts = {
            Phase.FOUNDATION: f"""あなたはエンジニアのスキル診断を行う専門家です。
現在は「基礎スキル診断」フェーズです。

以下の項目を効率的に評価してください:
- プログラミング経験
- データ構造・アルゴリズムの理解度
- Git/バージョン管理の経験

{base_instruction}""",
            Phase.DOMAIN: f"""あなたはエンジニアのキャリア診断を行う専門家です。
現在は「専攻領域選定」フェーズです。

以下の領域への適性と興味を判定してください:
- フロントエンド / バックエンド / フルスタック
- DevOps / インフラ
- 機械学習 / データサイエンス
- モバイル開発

{base_instruction}""",
            Phase.TECHNICAL: f"""あなたはエンジニアの技術スキル診断を行う専門家です。
現在は「詳細技術診断」フェーズです。

選定された領域に関する具体的な技術スキルを評価してください:
- 使用フレームワーク・ライブラリ
- 開発ツール・環境
- 設計パターンの理解

{base_instruction}""",
            Phase.ARCHITECTURE: f"""あなたはソフトウェアアーキテクチャの専門家です。
現在は「アーキテクチャ適性」フェーズです。

システム設計能力を評価してください:
- スケーラビリティの考慮
- セキュリティ・データモデリング
- アーキテクチャパターンの理解

{base_instruction}""",
            Phase.ROADMAP: f"""あなたは学習ロードマップの専門家です。
現在は「学習ロードマップ生成」フェーズです。

これまでの診断結果を踏まえて、学習目標を確認してください。

{base_instruction}""",
        }
        return prompts.get(phase, f"診断を進めてください。\n{base_instruction}")

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

    def _format_answers(
        self, answers: list[Answer], supplement: Optional[str]
    ) -> str:
        """Format user answers into a readable string."""
        parts = []
        for answer in answers:
            selected = ", ".join(answer.selected_options)
            parts.append(f"質問{answer.question_id}: {selected}")

        if supplement:
            parts.append(f"補足: {supplement}")

        return "\n".join(parts)

    def _format_user_message(
        self, content: str, answers: Optional[list[dict[str, Any]]]
    ) -> str:
        """Format a user message with answers for context."""
        if not answers:
            return content

        parts = [content] if content else []
        for answer in answers:
            question_id = answer.get("question_id", "?")
            selected = ", ".join(answer.get("selected_options", []))
            parts.append(f"Q{question_id}: {selected}")

        return "\n".join(parts)

    def _parse_structured_response(self, response_text: str) -> StructuredResponse:
        """Parse LLM response into a StructuredResponse."""
        parsed = self._parse_json_response(response_text)

        if not parsed:
            # Fallback if JSON parsing fails
            return StructuredResponse(
                message=response_text,
                questions=[],
                should_advance=False,
            )

        # Extract message
        message = parsed.get("message", "")

        # Extract questions
        questions = []
        for q_data in parsed.get("questions", []):
            options = [
                QuestionOption(id=opt.get("id", ""), label=opt.get("label", ""))
                for opt in q_data.get("options", [])
            ]
            question = Question(
                id=q_data.get("id", ""),
                text=q_data.get("text", ""),
                type=q_data.get("type", "single"),
                options=options,
            )
            questions.append(question)

        # Extract should_advance flag
        should_advance = parsed.get("should_advance", False)

        return StructuredResponse(
            message=message,
            questions=questions,
            should_advance=should_advance,
        )

    def _parse_json_response(self, response_text: str) -> Optional[dict[str, Any]]:
        """Parse JSON from LLM response."""
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

        return None
