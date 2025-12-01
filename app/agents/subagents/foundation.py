"""Foundation Skills Assessor Sub-Agent."""

import json
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.tools.assessment import assess_foundation_skills


class FoundationAssessorAgent:
    """Sub-agent specialized in assessing programming fundamentals."""

    SYSTEM_PROMPT = """あなたは基礎スキル評価の専門家です。学習者のプログラミング基礎力を深く診断します。

## 評価対象
1. **プログラミング言語理解**
   - 基本構文、制御フロー
   - オブジェクト指向プログラミング
   - 関数型プログラミングの概念

2. **アルゴリズム**
   - 計算量（Big O記法）の理解
   - 基本的なソートと検索
   - 問題解決アプローチ

3. **データ構造**
   - 配列、リスト、スタック、キュー
   - ハッシュテーブル、ツリー、グラフ
   - 適切なデータ構造の選択

## 評価プロセス
1. 各領域について質問を行う
2. 回答の深さと正確さを評価する
3. フォローアップ質問で理解度を確認する
4. 最終的なスコア（0-10）を提供する

## スコアリング基準
- 0-2: 未経験 - 基本概念の学習が必要
- 3-4: 初心者 - 基本は理解しているが実践経験が少ない
- 5-6: 中級者 - 実践的なコードが書ける
- 7-8: 上級者 - 複雑な問題を効率的に解決できる
- 9-10: エキスパート - 深い理解と最適化ができる

質問は具体的に、回答には根拠を求めてください。"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key
        self.conversation_history: list = []
        self.assessment_data: dict = {
            "programming": None,
            "algorithms": None,
            "data_structures": None,
        }

    def _get_llm(self) -> ChatAnthropic:
        """Get LLM instance."""
        return ChatAnthropic(
            model=self.model,
            api_key=self.api_key,
        )

    async def start_assessment(self) -> str:
        """Start the foundation assessment."""
        self.conversation_history = [
            SystemMessage(content=self.SYSTEM_PROMPT),
        ]

        initial_message = """基礎スキル診断を開始します。

まず、プログラミング経験についてお聞きします。

1. **主に使用しているプログラミング言語**は何ですか？その言語での経験年数も教えてください。

2. 最近取り組んだ**プロジェクトやコード**について、簡単に説明してください。どのような技術を使いましたか？

お気軽にお答えください。回答に基づいて、より詳しい質問をしていきます。"""

        self.conversation_history.append(AIMessage(content=initial_message))
        return initial_message

    async def process_response(self, user_response: str) -> str:
        """Process user response and generate next question or assessment."""
        self.conversation_history.append(HumanMessage(content=user_response))

        llm = self._get_llm()

        # Add context about what to do next
        context_message = HumanMessage(
            content=f"""学習者の回答: {user_response}

この回答を分析して：
1. 回答から読み取れるスキルレベルを評価してください
2. より深い理解を確認するためのフォローアップ質問を生成してください
3. まだ評価していない領域があれば、その質問も含めてください

現在の評価状況：
- プログラミング: {"評価済み" if self.assessment_data["programming"] else "未評価"}
- アルゴリズム: {"評価済み" if self.assessment_data["algorithms"] else "未評価"}
- データ構造: {"評価済み" if self.assessment_data["data_structures"] else "未評価"}

すべての領域を評価したら、総合評価を提供してください。"""
        )

        messages = self.conversation_history + [context_message]
        response = await llm.ainvoke(messages)

        self.conversation_history.append(AIMessage(content=response.content))
        return response.content

    async def get_questions_for_area(self, area: str) -> str:
        """Get assessment questions for a specific area."""
        result = assess_foundation_skills.invoke({"assessment_type": area})
        return result

    async def evaluate_area(self, area: str, responses: list[str]) -> dict:
        """Evaluate a specific area based on responses."""
        llm = self._get_llm()

        evaluation_prompt = f"""以下の回答を評価してください。

評価領域: {area}
学習者の回答:
{chr(10).join(f"- {r}" for r in responses)}

以下のJSON形式で評価を返してください：
{{
    "area": "{area}",
    "score": <0-10のスコア>,
    "level": "<beginner/intermediate/advanced/expert>",
    "strengths": ["強み1", "強み2"],
    "gaps": ["弱点1", "弱点2"],
    "recommendations": ["推奨1", "推奨2"]
}}"""

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=evaluation_prompt),
        ]

        response = await llm.ainvoke(messages)

        try:
            # Extract JSON from response
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                evaluation = json.loads(content[start:end])
                self.assessment_data[area] = evaluation
                return evaluation
        except json.JSONDecodeError:
            pass

        return {
            "area": area,
            "score": 5,
            "level": "intermediate",
            "error": "評価の解析に失敗しました",
        }

    async def generate_final_assessment(self) -> dict:
        """Generate final foundation assessment."""
        llm = self._get_llm()

        assessment_prompt = f"""これまでの診断結果に基づいて、最終的な基礎スキル評価を生成してください。

評価データ:
{json.dumps(self.assessment_data, ensure_ascii=False, indent=2)}

会話履歴から得られた追加の洞察も考慮してください。

以下のJSON形式で最終評価を返してください：
{{
    "overall_score": <0-10の総合スコア>,
    "overall_level": "<beginner/intermediate/advanced/expert>",
    "programming": {{
        "score": <スコア>,
        "notes": "評価コメント"
    }},
    "algorithms": {{
        "score": <スコア>,
        "notes": "評価コメント"
    }},
    "data_structures": {{
        "score": <スコア>,
        "notes": "評価コメント"
    }},
    "summary": "総合評価の説明",
    "next_steps": ["次のステップ1", "次のステップ2"]
}}"""

        messages = self.conversation_history + [HumanMessage(content=assessment_prompt)]
        response = await llm.ainvoke(messages)

        try:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        # Fallback assessment
        scores = [
            self.assessment_data.get(area, {}).get("score", 5)
            for area in ["programming", "algorithms", "data_structures"]
            if self.assessment_data.get(area)
        ]
        avg_score = sum(scores) / len(scores) if scores else 5

        return {
            "overall_score": avg_score,
            "overall_level": self._score_to_level(avg_score),
            "programming": self.assessment_data.get("programming", {}),
            "algorithms": self.assessment_data.get("algorithms", {}),
            "data_structures": self.assessment_data.get("data_structures", {}),
            "summary": "基礎スキル診断が完了しました。",
            "next_steps": ["次のフェーズ（領域適性診断）に進みます"],
        }

    def _score_to_level(self, score: float) -> str:
        """Convert score to level string."""
        if score < 3:
            return "beginner"
        elif score < 6:
            return "intermediate"
        elif score < 8:
            return "advanced"
        else:
            return "expert"

    def reset(self) -> None:
        """Reset the agent state."""
        self.conversation_history = []
        self.assessment_data = {
            "programming": None,
            "algorithms": None,
            "data_structures": None,
        }
