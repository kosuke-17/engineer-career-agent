"""SubAgent Middleware for delegating specialized assessments."""

from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm


@dataclass
class SubAgentConfig:
    """Configuration for a sub-agent."""

    name: str
    description: str
    system_prompt: str
    tools: list = field(default_factory=list)
    model: Optional[str] = None  # None means use default from factory


class SubAgentMiddleware:
    """Middleware for managing and delegating to specialized sub-agents."""

    def __init__(self):
        self.subagents: dict[str, SubAgentConfig] = {}
        self._register_default_subagents()

    def _register_default_subagents(self) -> None:
        """Register default sub-agents for diagnosis."""
        self.register_subagent(
            SubAgentConfig(
                name="foundation-assessor",
                description="Conducts in-depth assessment of programming fundamentals",
                system_prompt="""あなたは基礎スキル評価の専門家です。あなたの役割は：

1. プログラミング基礎についての的を絞った質問をする
2. アルゴリズムとデータ構造の理解度を評価する
3. 強みとギャップを特定する
4. 基礎スキルスコア（0-10）を提供する

知識の深さを理解するために、必ずフォローアップの質問をしてください。

評価基準：
- 0-3: 初心者 - 基本的な概念を学習中
- 4-6: 中級者 - 実践的なコードが書ける
- 7-8: 上級者 - 複雑な問題を解決できる
- 9-10: エキスパート - 深い理解と最適化ができる""",
            )
        )

        self.register_subagent(
            SubAgentConfig(
                name="domain-matcher",
                description="Evaluates aptitude for different engineering domains",
                system_prompt="""あなたは領域適性評価の専門家です。以下に基づいて評価を行います：

1. 基礎スキル
2. 興味・関心
3. 問題解決パターン

以下の領域への適性を0-10でスコアリングしてください：
- フロントエンド開発
- バックエンド開発
- DevOps/インフラ
- 機械学習エンジニアリング
- システム設計

各領域について、学習者の回答から適性の根拠を示してください。""",
            )
        )

        self.register_subagent(
            SubAgentConfig(
                name="technical-analyzer",
                description="Analyzes technical skills in specific domain",
                system_prompt="""あなたは技術スキル分析の専門家です。選定された領域について：

1. 習得すべき主要技術を特定する
2. 各技術の現在の知識レベルを評価する
3. 学習の順序を推奨する
4. 実践的なプロジェクトを提案する

技術スタックの深い理解を確認するため、具体的な質問をしてください。
実際の経験とプロジェクトについて聞いてください。""",
            )
        )

        self.register_subagent(
            SubAgentConfig(
                name="architecture-assessor",
                description="Assesses system design and architecture thinking",
                system_prompt="""あなたはアーキテクチャ評価の専門家です。以下を評価します：

1. システム設計の理解度
2. スケーラビリティへの意識
3. トレードオフの判断能力
4. 設計パターンの知識

実際の設計課題を出して、思考プロセスを評価してください。
正解よりも、どのように考えるかを重視してください。""",
            )
        )

    def register_subagent(self, config: SubAgentConfig) -> None:
        """Register a sub-agent configuration."""
        self.subagents[config.name] = config

    def get_system_prompt_addition(self) -> str:
        """Get system prompt addition for sub-agent delegation."""
        subagent_list = "\n".join(
            f"- **{name}**: {config.description}" for name, config in self.subagents.items()
        )

        return f"""
## サブエージェントへの委譲

以下の専門サブエージェントに診断を委譲できます：

{subagent_list}

`delegate_to_subagent` ツールを使用して、専門的な診断を委譲してください。
各サブエージェントは特定の領域に特化しており、より深い診断を行います。
"""

    async def delegate_to_subagent(
        self,
        subagent_name: str,
        context: str,
        user_message: str,
    ) -> dict:
        """
        Delegate a task to a specialized sub-agent.

        Args:
            subagent_name: Name of the sub-agent to delegate to
            context: Context information for the sub-agent
            user_message: User's message/response to process

        Returns:
            Dictionary with sub-agent response
        """
        if subagent_name not in self.subagents:
            return {
                "success": False,
                "error": f"Unknown sub-agent: {subagent_name}",
                "available_subagents": list(self.subagents.keys()),
            }

        config = self.subagents[subagent_name]

        try:
            llm = get_llm(model=config.model)

            messages = [
                SystemMessage(content=config.system_prompt),
                HumanMessage(content=f"コンテキスト:\n{context}\n\n学習者の回答:\n{user_message}"),
            ]

            response = await llm.ainvoke(messages)

            return {
                "success": True,
                "subagent": subagent_name,
                "response": response.content,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "subagent": subagent_name,
            }

    def get_subagent_info(self, name: str) -> Optional[dict]:
        """Get information about a specific sub-agent."""
        if name not in self.subagents:
            return None

        config = self.subagents[name]
        return {
            "name": config.name,
            "description": config.description,
            "model": config.model,
        }

    def list_subagents(self) -> list[dict]:
        """List all registered sub-agents."""
        return [
            {
                "name": config.name,
                "description": config.description,
            }
            for config in self.subagents.values()
        ]


class SubAgentOrchestrator:
    """Orchestrates multiple sub-agents for complex assessments."""

    def __init__(self, middleware: SubAgentMiddleware):
        self.middleware = middleware
        self.assessment_results: dict[str, Any] = {}

    async def run_foundation_assessment(self, context: str, user_responses: list[str]) -> dict:
        """Run foundation skills assessment."""
        combined_responses = "\n\n".join(user_responses)
        result = await self.middleware.delegate_to_subagent(
            "foundation-assessor",
            context,
            combined_responses,
        )
        if result["success"]:
            self.assessment_results["foundation"] = result["response"]
        return result

    async def run_domain_matching(self, foundation_result: str, user_responses: list[str]) -> dict:
        """Run domain aptitude matching."""
        context = f"基礎スキル診断結果:\n{foundation_result}"
        combined_responses = "\n\n".join(user_responses)
        result = await self.middleware.delegate_to_subagent(
            "domain-matcher",
            context,
            combined_responses,
        )
        if result["success"]:
            self.assessment_results["domain"] = result["response"]
        return result

    async def run_technical_analysis(self, domain: str, user_responses: list[str]) -> dict:
        """Run technical skills analysis for specific domain."""
        context = f"選定領域: {domain}\n以前の診断結果: {self.assessment_results}"
        combined_responses = "\n\n".join(user_responses)
        result = await self.middleware.delegate_to_subagent(
            "technical-analyzer",
            context,
            combined_responses,
        )
        if result["success"]:
            self.assessment_results["technical"] = result["response"]
        return result

    async def run_architecture_assessment(self, user_responses: list[str]) -> dict:
        """Run architecture thinking assessment."""
        context = f"以前の診断結果: {self.assessment_results}"
        combined_responses = "\n\n".join(user_responses)
        result = await self.middleware.delegate_to_subagent(
            "architecture-assessor",
            context,
            combined_responses,
        )
        if result["success"]:
            self.assessment_results["architecture"] = result["response"]
        return result

    def get_all_results(self) -> dict:
        """Get all assessment results."""
        return self.assessment_results.copy()
