"""Domain Matcher Sub-Agent."""

import json
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.llm import get_llm
from app.tools.assessment import assess_domain_aptitude


class DomainMatcherAgent:
    """Sub-agent specialized in evaluating domain aptitude."""

    SYSTEM_PROMPT = """あなたは領域適性評価の専門家です。学習者に最適なエンジニアリング領域を特定します。

## 評価対象領域
1. **フロントエンド開発**
   - UI/UXへの関心
   - ビジュアル思考
   - ユーザー視点

2. **バックエンド開発**
   - システム設計
   - データモデリング
   - パフォーマンス最適化

3. **DevOps/インフラ**
   - 自動化への関心
   - システム運用
   - セキュリティ意識

4. **機械学習エンジニアリング**
   - 数学・統計への関心
   - データドリブン思考
   - 実験的アプローチ

5. **モバイル開発**
   - クロスプラットフォーム
   - ユーザー体験
   - パフォーマンス制約

## 評価プロセス
1. 興味・関心を探る質問
2. 過去の経験やプロジェクトの確認
3. 問題解決スタイルの把握
4. 各領域への適性スコアリング（0-10）

質問は学習者の自然な傾向を引き出すようにしてください。"""

    DOMAIN_DESCRIPTIONS = {
        "frontend": {
            "name": "フロントエンド開発",
            "keywords": [
                "UI",
                "UX",
                "デザイン",
                "アニメーション",
                "レスポンシブ",
                "ユーザー体験",
            ],
            "indicators": [
                "ビジュアルへのこだわり",
                "ユーザー視点",
                "インタラクション",
            ],
        },
        "backend": {
            "name": "バックエンド開発",
            "keywords": [
                "API",
                "データベース",
                "サーバー",
                "スケーラビリティ",
                "セキュリティ",
            ],
            "indicators": ["論理的思考", "システム全体の把握", "パフォーマンス意識"],
        },
        "devops": {
            "name": "DevOps/インフラ",
            "keywords": ["自動化", "CI/CD", "クラウド", "コンテナ", "監視"],
            "indicators": ["自動化への情熱", "運用視点", "効率化"],
        },
        "ml_engineering": {
            "name": "機械学習エンジニアリング",
            "keywords": ["データ", "モデル", "統計", "予測", "最適化"],
            "indicators": ["数学への関心", "データ分析", "実験的思考"],
        },
        "mobile": {
            "name": "モバイル開発",
            "keywords": ["iOS", "Android", "React Native", "Flutter", "アプリ"],
            "indicators": ["モバイルUX", "オフライン対応", "バッテリー効率"],
        },
    }

    def __init__(
        self,
        model: Optional[str] = None,
    ):
        self.model = model
        self.conversation_history: list = []
        self.domain_scores: dict[str, float] = {}
        self.foundation_context: Optional[dict] = None

    def _get_llm(self) -> BaseChatModel:
        """Get LLM instance using the factory."""
        return get_llm(model=self.model)

    async def start_assessment(self, foundation_result: Optional[dict] = None) -> str:
        """Start the domain aptitude assessment."""
        self.foundation_context = foundation_result
        self.conversation_history = [
            SystemMessage(content=self.SYSTEM_PROMPT),
        ]

        context_info = ""
        if foundation_result:
            context_info = f"""
基礎スキル診断の結果：
- 総合スコア: {foundation_result.get("overall_score", "N/A")}/10
- レベル: {foundation_result.get("overall_level", "N/A")}
"""

        initial_message = f"""領域適性診断を開始します。
{context_info}
あなたに最適なエンジニアリング領域を見つけるために、いくつか質問させてください。

**質問1: 興味・関心について**

プログラミングで何かを作るとき、どの部分に最もワクワクしますか？

例えば：
- ユーザーが直接触れる画面やインターフェースを作ること
- 裏側で動くロジックやデータの処理を設計すること
- システム全体を効率的に動かす仕組みを構築すること
- データから価値ある洞察を引き出すこと

自由にお答えください。"""

        self.conversation_history.append(AIMessage(content=initial_message))
        return initial_message

    async def process_response(self, user_response: str) -> str:
        """Process user response and continue assessment."""
        self.conversation_history.append(HumanMessage(content=user_response))

        llm = self._get_llm()

        # Analyze response for domain indicators
        analysis_prompt = HumanMessage(
            content=f"""学習者の回答を分析してください：

回答: {user_response}

1. この回答から読み取れる領域への傾向を分析してください
2. さらに適性を明確にするための次の質問を生成してください
3. 質問は自然で、学習者が答えやすいものにしてください

まだ十分な情報がない場合は、追加の質問をしてください。
十分な情報が集まったら、各領域の適性スコアを提示する準備をしてください。"""
        )

        messages = self.conversation_history + [analysis_prompt]
        response = await llm.ainvoke(messages)

        self.conversation_history.append(AIMessage(content=response.content))
        return response.content

    async def get_domain_questions(self, domains: str) -> str:
        """Get questions for specific domains."""
        result = assess_domain_aptitude.invoke({"domains": domains})
        return result

    async def evaluate_domains(self, responses: list[str]) -> dict:
        """Evaluate all domains based on collected responses."""
        llm = self._get_llm()

        evaluation_prompt = f"""これまでの会話と回答に基づいて、各領域への適性を評価してください。

学習者の回答:
{chr(10).join(f"- {r}" for r in responses)}

基礎スキル情報:
{json.dumps(self.foundation_context, ensure_ascii=False, indent=2) if self.foundation_context else "なし"}

以下のJSON形式で各領域の適性を評価してください：
{{
    "frontend": {{
        "score": <0-10>,
        "reasoning": "理由の説明",
        "indicators": ["見られた適性指標"]
    }},
    "backend": {{
        "score": <0-10>,
        "reasoning": "理由の説明",
        "indicators": ["見られた適性指標"]
    }},
    "devops": {{
        "score": <0-10>,
        "reasoning": "理由の説明",
        "indicators": ["見られた適性指標"]
    }},
    "ml_engineering": {{
        "score": <0-10>,
        "reasoning": "理由の説明",
        "indicators": ["見られた適性指標"]
    }},
    "mobile": {{
        "score": <0-10>,
        "reasoning": "理由の説明",
        "indicators": ["見られた適性指標"]
    }},
    "recommended_domain": "<最も適性が高い領域>",
    "recommendation_reason": "推奨理由の詳細説明"
}}"""

        messages = self.conversation_history + [HumanMessage(content=evaluation_prompt)]
        response = await llm.ainvoke(messages)

        try:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                evaluation = json.loads(content[start:end])
                self.domain_scores = {
                    domain: data.get("score", 0)
                    for domain, data in evaluation.items()
                    if isinstance(data, dict) and "score" in data
                }
                return evaluation
        except json.JSONDecodeError:
            pass

        # Fallback
        return {
            "recommended_domain": "backend",
            "recommendation_reason": "評価データの解析に問題がありました。デフォルトでバックエンドを推奨します。",
        }

    async def generate_final_assessment(self) -> dict:
        """Generate final domain assessment."""
        llm = self._get_llm()

        assessment_prompt = f"""これまでの診断に基づいて、最終的な領域適性評価を生成してください。

現在のスコア:
{json.dumps(self.domain_scores, ensure_ascii=False, indent=2)}

以下のJSON形式で最終評価を返してください：
{{
    "domain_scores": {{
        "frontend": <スコア>,
        "backend": <スコア>,
        "devops": <スコア>,
        "ml_engineering": <スコア>,
        "mobile": <スコア>
    }},
    "primary_recommendation": "<最も適した領域>",
    "secondary_recommendation": "<2番目に適した領域>",
    "summary": "総合評価の説明",
    "career_path_suggestion": "キャリアパスの提案"
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

        # Find highest scoring domain
        if self.domain_scores:
            primary = max(self.domain_scores, key=self.domain_scores.get)
            scores_sorted = sorted(self.domain_scores.items(), key=lambda x: x[1], reverse=True)
            secondary = scores_sorted[1][0] if len(scores_sorted) > 1 else primary
        else:
            primary = "backend"
            secondary = "frontend"

        return {
            "domain_scores": self.domain_scores
            or {
                "frontend": 5,
                "backend": 6,
                "devops": 4,
                "ml_engineering": 4,
                "mobile": 4,
            },
            "primary_recommendation": primary,
            "secondary_recommendation": secondary,
            "summary": "領域適性診断が完了しました。",
            "career_path_suggestion": f"{self.DOMAIN_DESCRIPTIONS.get(primary, {}).get('name', primary)}を中心としたキャリアパスを推奨します。",
        }

    def reset(self) -> None:
        """Reset the agent state."""
        self.conversation_history = []
        self.domain_scores = {}
        self.foundation_context = None
