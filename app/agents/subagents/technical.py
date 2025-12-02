"""Technical Analyzer Sub-Agent."""

import json
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.llm import get_llm
from app.tools.assessment import assess_technical_depth, fetch_learning_resources


class TechnicalAnalyzerAgent:
    """Sub-agent specialized in analyzing technical skills for specific domains."""

    SYSTEM_PROMPT = """あなたは技術スキル分析の専門家です。特定のエンジニアリング領域における技術スタックの習熟度を深く分析します。

## 分析対象

### バックエンド技術
- プログラミング言語: Python, Java, Go, Node.js
- フレームワーク: FastAPI, Django, Spring Boot, Express
- データベース: PostgreSQL, MySQL, MongoDB, Redis
- API設計: REST, GraphQL, gRPC

### フロントエンド技術
- 言語: JavaScript, TypeScript
- フレームワーク: React, Vue, Angular, Next.js
- スタイリング: CSS, Tailwind, styled-components
- 状態管理: Redux, Zustand, Recoil

### DevOps技術
- コンテナ: Docker, Kubernetes
- CI/CD: GitHub Actions, Jenkins, CircleCI
- クラウド: AWS, GCP, Azure
- IaC: Terraform, Pulumi

## 評価プロセス
1. 選定領域の主要技術を特定
2. 各技術の経験と理解度を質問
3. 実践的な知識を確認する質問
4. 学習優先度と推奨リソースを提案

実際のプロジェクト経験に基づいた具体的な質問をしてください。"""

    TECH_STACKS = {
        "backend": {
            "core": ["Python", "SQL", "REST API"],
            "frameworks": ["FastAPI", "Django", "Flask"],
            "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
            "tools": ["Docker", "Git", "Linux"],
        },
        "frontend": {
            "core": ["JavaScript", "TypeScript", "HTML/CSS"],
            "frameworks": ["React", "Vue", "Next.js"],
            "tools": ["npm/yarn", "Webpack/Vite", "Testing Library"],
            "concepts": ["State Management", "Responsive Design", "Accessibility"],
        },
        "devops": {
            "core": ["Linux", "Shell Script", "Networking"],
            "containers": ["Docker", "Kubernetes"],
            "ci_cd": ["GitHub Actions", "Jenkins", "ArgoCD"],
            "cloud": ["AWS", "GCP", "Azure"],
            "iac": ["Terraform", "Ansible", "Pulumi"],
        },
        "ml_engineering": {
            "core": ["Python", "Statistics", "Linear Algebra"],
            "libraries": ["NumPy", "Pandas", "scikit-learn"],
            "deep_learning": ["TensorFlow", "PyTorch"],
            "mlops": ["MLflow", "Kubeflow", "DVC"],
        },
    }

    def __init__(
        self,
        model: Optional[str] = None,
    ):
        self.model = model
        self.conversation_history: list = []
        self.selected_domain: Optional[str] = None
        self.tech_assessments: dict = {}
        self.previous_context: dict = {}

    def _get_llm(self) -> BaseChatModel:
        """Get LLM instance using the factory."""
        return get_llm(model=self.model)

    async def start_assessment(
        self,
        domain: str,
        foundation_result: Optional[dict] = None,
        domain_result: Optional[dict] = None,
    ) -> str:
        """Start the technical skills assessment for a specific domain."""
        self.selected_domain = domain.lower().replace(" ", "_")
        self.previous_context = {
            "foundation": foundation_result,
            "domain": domain_result,
        }
        self.conversation_history = [
            SystemMessage(content=self.SYSTEM_PROMPT),
        ]

        domain_name = {
            "backend": "バックエンド開発",
            "frontend": "フロントエンド開発",
            "devops": "DevOps/インフラ",
            "ml_engineering": "機械学習エンジニアリング",
        }.get(self.selected_domain, domain)

        tech_stack = self.TECH_STACKS.get(self.selected_domain, {})
        core_techs = tech_stack.get("core", [])

        initial_message = f"""**{domain_name}**の技術スキル診断を開始します。

この領域で習得すべき主要な技術について、あなたの経験と理解度を確認させてください。

**質問1: コア技術の経験**

{domain_name}の基盤となる技術（{", ".join(core_techs)}）について：

1. これらの技術の中で、最も経験が長いものは何ですか？
2. その技術を使って、どのようなプロジェクトや機能を実装しましたか？
3. 自己評価で、その技術のレベルはどの程度だと思いますか？
   （初心者 / 中級者 / 上級者 / エキスパート）

具体的に教えてください。"""

        self.conversation_history.append(AIMessage(content=initial_message))
        return initial_message

    async def process_response(self, user_response: str) -> str:
        """Process user response and continue assessment."""
        self.conversation_history.append(HumanMessage(content=user_response))

        llm = self._get_llm()

        tech_stack = self.TECH_STACKS.get(self.selected_domain, {})
        all_techs = []
        for category_techs in tech_stack.values():
            all_techs.extend(category_techs)

        assessed_techs = list(self.tech_assessments.keys())
        remaining_techs = [t for t in all_techs if t not in assessed_techs]

        analysis_prompt = HumanMessage(
            content=f"""学習者の回答を分析してください：

回答: {user_response}

選定領域: {self.selected_domain}
評価済み技術: {assessed_techs}
未評価技術: {remaining_techs[:5]}  # 上位5つ

1. この回答から特定できる技術スキルレベルを評価してください
2. より深い理解を確認するための技術的な質問を生成してください
3. まだ評価していない重要な技術があれば、その質問も含めてください

実践的な経験を引き出す質問を心がけてください。"""
        )

        messages = self.conversation_history + [analysis_prompt]
        response = await llm.ainvoke(messages)

        self.conversation_history.append(AIMessage(content=response.content))
        return response.content

    async def get_tech_questions(self, technologies: str) -> str:
        """Get questions for specific technologies."""
        result = assess_technical_depth.invoke(
            {
                "domain": self.selected_domain or "backend",
                "technologies": technologies,
            }
        )
        return result

    async def get_learning_resources(
        self, skill_level: str, topic: str, preferred_format: str
    ) -> str:
        """Get learning resources for a topic."""
        result = fetch_learning_resources.invoke(
            {
                "skill_level": skill_level,
                "topic": topic,
                "preferred_format": preferred_format,
            }
        )
        return result

    async def evaluate_technology(self, tech: str, responses: list[str]) -> dict:
        """Evaluate a specific technology based on responses."""
        llm = self._get_llm()

        evaluation_prompt = f"""以下の回答から「{tech}」のスキルレベルを評価してください。

回答:
{chr(10).join(f"- {r}" for r in responses)}

以下のJSON形式で評価を返してください：
{{
    "technology": "{tech}",
    "score": <0-10>,
    "level": "<beginner/intermediate/advanced/expert>",
    "experience_years": <推定経験年数>,
    "strengths": ["強み1", "強み2"],
    "gaps": ["弱点1", "弱点2"],
    "learning_priority": "<high/medium/low>",
    "recommended_resources": ["リソース1", "リソース2"]
}}"""

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=evaluation_prompt),
        ]

        response = await llm.ainvoke(messages)

        try:
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                evaluation = json.loads(content[start:end])
                self.tech_assessments[tech] = evaluation
                return evaluation
        except json.JSONDecodeError:
            pass

        return {
            "technology": tech,
            "score": 5,
            "level": "intermediate",
            "error": "評価の解析に失敗しました",
        }

    async def generate_final_assessment(self) -> dict:
        """Generate final technical assessment with learning recommendations."""
        llm = self._get_llm()

        tech_stack = self.TECH_STACKS.get(self.selected_domain, {})

        assessment_prompt = f"""これまでの診断に基づいて、最終的な技術スキル評価と学習推奨を生成してください。

選定領域: {self.selected_domain}
技術スタック構成:
{json.dumps(tech_stack, ensure_ascii=False, indent=2)}

評価済み技術:
{json.dumps(self.tech_assessments, ensure_ascii=False, indent=2)}

以前の診断結果:
{json.dumps(self.previous_context, ensure_ascii=False, indent=2)}

以下のJSON形式で最終評価を返してください：
{{
    "domain": "{self.selected_domain}",
    "overall_technical_score": <0-10の総合スコア>,
    "technology_scores": {{
        "<技術名>": {{
            "score": <スコア>,
            "level": "<レベル>",
            "priority": "<学習優先度>"
        }}
    }},
    "strongest_technologies": ["得意技術1", "得意技術2"],
    "priority_learning": ["優先学習技術1", "優先学習技術2"],
    "learning_path": [
        {{
            "order": 1,
            "technology": "<技術名>",
            "duration": "<推奨学習期間>",
            "resources": ["リソース1", "リソース2"]
        }}
    ],
    "project_suggestions": [
        {{
            "name": "<プロジェクト名>",
            "description": "<説明>",
            "technologies": ["使用技術"],
            "difficulty": "<easy/medium/hard>"
        }}
    ],
    "summary": "総合評価と推奨の説明"
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
            data.get("score", 5)
            for data in self.tech_assessments.values()
            if isinstance(data, dict)
        ]
        avg_score = sum(scores) / len(scores) if scores else 5

        return {
            "domain": self.selected_domain,
            "overall_technical_score": avg_score,
            "technology_scores": self.tech_assessments,
            "strongest_technologies": [],
            "priority_learning": list(tech_stack.get("core", []))[:3],
            "learning_path": [],
            "project_suggestions": [],
            "summary": "技術スキル診断が完了しました。",
        }

    def reset(self) -> None:
        """Reset the agent state."""
        self.conversation_history = []
        self.selected_domain = None
        self.tech_assessments = {}
        self.previous_context = {}
