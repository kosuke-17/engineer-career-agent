"""Main Deep Agent for Learning Path Customization."""

from typing import Optional, Any
from datetime import datetime
import json
import uuid

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool

from app.config import get_settings
from app.storage.file_backend import FileBackend
from app.storage.schemas import (
    LearnerProfile,
    AssessmentResult,
    PhaseResult,
    SkillScore,
    DomainAptitude,
    EngineeringDomain,
    SkillLevel,
    LearningStyle,
)
from app.agents.middleware.todolist import TodoListMiddleware
from app.agents.middleware.filesystem import FilesystemMiddleware
from app.agents.middleware.subagent import SubAgentMiddleware, SubAgentOrchestrator
from app.agents.subagents.foundation import FoundationAssessorAgent
from app.agents.subagents.domain import DomainMatcherAgent
from app.agents.subagents.technical import TechnicalAnalyzerAgent
from app.tools.roadmap import generate_learning_roadmap
from app.models.diagnosis import (
    DiagnosisSession,
    DiagnosisPhase,
    PhaseStatus,
    Message,
)


class LearningPathAgent:
    """Main agent for learning path customization using Deep Agent architecture."""

    SYSTEM_PROMPT = """あなたは高度な学習パスアドバイザー（Deep Agent）です。

## ミッション
1. 包括的なスキル診断を複数フェーズで実施
2. ファイルシステムメモリを使用して学習者プロファイルを詳細に管理
3. 専門的な診断を適切なサブエージェントに委譲
4. パーソナライズされた学習ロードマップを生成

## ワークフロー
1. **TodoList**を使用して診断フェーズを追跡
   - Phase 1: 基礎診断
   - Phase 2: 領域適性
   - Phase 3: 技術詳細
   - Phase 4: アーキテクチャ
   - Phase 5: ロードマップ生成

2. **Filesystem**を使用して：
   - `/memories/` から学習者の履歴を読み込む
   - `/current_session/` に診断中の情報を保存
   - 最終結果を `/memories/` に保存

3. **SubAgent**に委譲：
   - foundation-assessor: 基礎スキル診断
   - domain-matcher: キャリア方向性
   - technical-analyzer: 技術スタック分析

## 重要なルール
- 明確化のための質問をする
- Todo更新で推論を示す
- 学習者の回答に基づいて適応する
- 常に過去の学習履歴を参照する
- 励ましと具体的なアドバイスを提供する

日本語で応答してください。"""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        settings = get_settings()
        self.model = model or settings.default_model
        self.api_key = api_key or settings.anthropic_api_key

        # Initialize storage
        self.file_backend = FileBackend(
            memories_dir=settings.memories_dir,
            sessions_dir=settings.sessions_dir,
        )

        # Initialize middleware
        self.filesystem_middleware = FilesystemMiddleware(self.file_backend)
        self.subagent_middleware = SubAgentMiddleware(
            default_model=self.model,
            api_key=self.api_key,
        )

        # Initialize sub-agents
        self.foundation_agent = FoundationAssessorAgent(
            model=self.model,
            api_key=self.api_key,
        )
        self.domain_agent = DomainMatcherAgent(
            model=self.model,
            api_key=self.api_key,
        )
        self.technical_agent = TechnicalAnalyzerAgent(
            model=self.model,
            api_key=self.api_key,
        )

        # Session management
        self.sessions: dict[str, DiagnosisSession] = {}
        self.todo_middlewares: dict[str, TodoListMiddleware] = {}
        self.assessment_data: dict[str, dict] = {}

    def _get_llm(self) -> ChatAnthropic:
        """Get LLM instance."""
        return ChatAnthropic(
            model=self.model,
            api_key=self.api_key,
            max_tokens=4096,
        )

    async def start_session(
        self,
        user_id: str,
        initial_message: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Start a new diagnosis session.

        Args:
            user_id: User identifier
            initial_message: Optional initial message from user

        Returns:
            Tuple of (session_id, initial_response)
        """
        session_id = str(uuid.uuid4())

        # Create session
        session = DiagnosisSession(
            session_id=session_id,
            user_id=user_id,
        )
        self.sessions[session_id] = session

        # Initialize todo middleware for this session
        self.todo_middlewares[session_id] = TodoListMiddleware(session_id)

        # Initialize assessment data
        self.assessment_data[session_id] = {
            "foundation": None,
            "domain": None,
            "technical": None,
            "architecture": None,
            "roadmap": None,
        }

        # Mark first phase as in progress
        if session.phases:
            session.phases[0].status = PhaseStatus.IN_PROGRESS
            session.phases[0].started_at = datetime.now()

        # Load user context
        user_context = await self.filesystem_middleware.load_user_context(user_id)
        context_prompt = self.filesystem_middleware.format_user_context_for_prompt(user_context)

        # Generate initial response
        llm = self._get_llm()

        todo_display = self.todo_middlewares[session_id].format_for_display()

        system_message = f"""{self.SYSTEM_PROMPT}

{context_prompt}

{todo_display}
"""

        messages = [
            SystemMessage(content=system_message),
        ]

        if initial_message:
            messages.append(HumanMessage(content=initial_message))
            session.add_message("user", initial_message)

        intro_prompt = """新しい診断セッションを開始します。

学習者を歓迎し、診断プロセスを説明してください。
その後、基礎スキル診断（Phase 1）を開始するための最初の質問をしてください。

まず学習者の名前、経験年数、現在の目標について簡単に聞いてください。"""

        messages.append(HumanMessage(content=intro_prompt))

        response = await llm.ainvoke(messages)
        response_text = response.content

        session.add_message("assistant", response_text)

        # Save session
        await self._save_session(session)

        return session_id, response_text

    async def process_message(
        self,
        session_id: str,
        user_message: str,
    ) -> str:
        """
        Process a user message in an existing session.

        Args:
            session_id: Session identifier
            user_message: User's message

        Returns:
            Assistant's response
        """
        if session_id not in self.sessions:
            return "セッションが見つかりません。新しいセッションを開始してください。"

        session = self.sessions[session_id]
        session.add_message("user", user_message)

        # Get current phase
        current_phase = session.current_phase
        todo_middleware = self.todo_middlewares.get(session_id)

        # Route to appropriate handler based on phase
        response = await self._handle_phase(
            session=session,
            user_message=user_message,
            phase=current_phase,
        )

        session.add_message("assistant", response)

        # Check if phase is complete and advance
        await self._check_phase_completion(session)

        # Save session
        await self._save_session(session)

        return response

    async def _handle_phase(
        self,
        session: DiagnosisSession,
        user_message: str,
        phase: DiagnosisPhase,
    ) -> str:
        """Handle message based on current phase."""
        session_id = session.session_id

        if phase == DiagnosisPhase.FOUNDATION:
            return await self._handle_foundation_phase(session, user_message)
        elif phase == DiagnosisPhase.DOMAIN:
            return await self._handle_domain_phase(session, user_message)
        elif phase == DiagnosisPhase.TECHNICAL:
            return await self._handle_technical_phase(session, user_message)
        elif phase == DiagnosisPhase.ARCHITECTURE:
            return await self._handle_architecture_phase(session, user_message)
        elif phase == DiagnosisPhase.ROADMAP:
            return await self._handle_roadmap_phase(session, user_message)
        else:
            return await self._generate_general_response(session, user_message)

    async def _handle_foundation_phase(
        self,
        session: DiagnosisSession,
        user_message: str,
    ) -> str:
        """Handle foundation assessment phase."""
        llm = self._get_llm()

        # Get conversation history for this phase
        phase_messages = self._get_phase_messages(session, DiagnosisPhase.FOUNDATION)

        system_content = f"""{self.SYSTEM_PROMPT}

現在のフェーズ: Phase 1 - 基礎スキル診断

このフェーズでは以下を評価します：
1. プログラミング言語の理解度
2. アルゴリズム・計算量の理解
3. データ構造の理解

学習者の回答を分析し、適切なフォローアップ質問をしてください。
十分な情報が集まったら、Phase 2（領域適性診断）への移行を提案してください。

診断は丁寧に、しかし効率的に進めてください。"""

        messages = [
            SystemMessage(content=system_content),
            *phase_messages,
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)
        return response.content

    async def _handle_domain_phase(
        self,
        session: DiagnosisSession,
        user_message: str,
    ) -> str:
        """Handle domain aptitude phase."""
        llm = self._get_llm()

        foundation_result = self.assessment_data.get(session.session_id, {}).get("foundation")
        foundation_context = ""
        if foundation_result:
            foundation_context = f"""
基礎スキル診断結果:
- 総合スコア: {foundation_result.get('overall_score', 'N/A')}/10
- プログラミング: {foundation_result.get('programming', {}).get('score', 'N/A')}/10
- アルゴリズム: {foundation_result.get('algorithms', {}).get('score', 'N/A')}/10
- データ構造: {foundation_result.get('data_structures', {}).get('score', 'N/A')}/10
"""

        system_content = f"""{self.SYSTEM_PROMPT}

現在のフェーズ: Phase 2 - 専攻領域選定
{foundation_context}

このフェーズでは以下の領域への適性を評価します：
- フロントエンド開発
- バックエンド開発
- DevOps/インフラ
- 機械学習エンジニアリング
- モバイル開発

学習者の興味、経験、問題解決スタイルを探る質問をしてください。
十分な情報が集まったら、最も適した領域を推奨し、Phase 3への移行を提案してください。"""

        phase_messages = self._get_phase_messages(session, DiagnosisPhase.DOMAIN)

        messages = [
            SystemMessage(content=system_content),
            *phase_messages,
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)
        return response.content

    async def _handle_technical_phase(
        self,
        session: DiagnosisSession,
        user_message: str,
    ) -> str:
        """Handle technical assessment phase."""
        llm = self._get_llm()

        domain_result = self.assessment_data.get(session.session_id, {}).get("domain")
        recommended_domain = "backend"
        if domain_result:
            recommended_domain = domain_result.get("primary_recommendation", "backend")

        system_content = f"""{self.SYSTEM_PROMPT}

現在のフェーズ: Phase 3 - 詳細技術診断
推奨領域: {recommended_domain}

このフェーズでは選定領域の具体的な技術スタックを評価します。
各技術の経験、理解度、実践的な知識を確認してください。

十分な情報が集まったら、Phase 4（アーキテクチャ適性）への移行を提案してください。"""

        phase_messages = self._get_phase_messages(session, DiagnosisPhase.TECHNICAL)

        messages = [
            SystemMessage(content=system_content),
            *phase_messages,
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)
        return response.content

    async def _handle_architecture_phase(
        self,
        session: DiagnosisSession,
        user_message: str,
    ) -> str:
        """Handle architecture assessment phase."""
        llm = self._get_llm()

        system_content = f"""{self.SYSTEM_PROMPT}

現在のフェーズ: Phase 4 - アーキテクチャ適性

このフェーズではシステム設計・アーキテクチャ思考能力を診断します：
- システム設計の理解
- スケーラビリティへの意識
- トレードオフの判断
- 設計パターンの知識

簡単な設計課題を出して、思考プロセスを評価してください。
十分な情報が集まったら、Phase 5（ロードマップ生成）への移行を提案してください。"""

        phase_messages = self._get_phase_messages(session, DiagnosisPhase.ARCHITECTURE)

        messages = [
            SystemMessage(content=system_content),
            *phase_messages,
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)
        return response.content

    async def _handle_roadmap_phase(
        self,
        session: DiagnosisSession,
        user_message: str,
    ) -> str:
        """Handle roadmap generation phase."""
        llm = self._get_llm()

        # Gather all assessment data
        assessment = self.assessment_data.get(session.session_id, {})

        # Generate roadmap using tool
        foundation_score = assessment.get("foundation", {}).get("overall_score", 5)
        domain_result = assessment.get("domain", {})
        recommended_domain = domain_result.get("primary_recommendation", "backend")
        technical_result = assessment.get("technical", {})

        # Get user preferences from context
        user_context = await self.filesystem_middleware.load_user_context(session.user_id)
        preferences = user_context.get("preferences", {})
        learning_style = preferences.get("preferred_learning_style", "project_based")
        weekly_hours = preferences.get("learning_hours_per_week", 10)

        # Generate roadmap
        roadmap_result = generate_learning_roadmap.invoke({
            "foundation_score": foundation_score,
            "recommended_domain": recommended_domain,
            "technical_assessment": json.dumps(technical_result),
            "learning_style": learning_style,
            "available_hours_per_week": weekly_hours,
        })

        roadmap_data = json.loads(roadmap_result)
        self.assessment_data[session.session_id]["roadmap"] = roadmap_data

        system_content = f"""{self.SYSTEM_PROMPT}

現在のフェーズ: Phase 5 - 学習ロードマップ生成

生成されたロードマップ:
{roadmap_result}

このロードマップを学習者に分かりやすく説明してください。
- 各フェーズの目標と期間
- 推奨プロジェクト
- 週間スケジュールの提案
- 成功のためのヒント

学習者の質問に答え、必要に応じてロードマップをカスタマイズする準備をしてください。"""

        phase_messages = self._get_phase_messages(session, DiagnosisPhase.ROADMAP)

        messages = [
            SystemMessage(content=system_content),
            *phase_messages,
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)

        # Mark session as complete
        session.is_complete = True

        return response.content

    async def _generate_general_response(
        self,
        session: DiagnosisSession,
        user_message: str,
    ) -> str:
        """Generate a general response."""
        llm = self._get_llm()

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]

        response = await llm.ainvoke(messages)
        return response.content

    def _get_phase_messages(
        self,
        session: DiagnosisSession,
        phase: DiagnosisPhase,
    ) -> list:
        """Get messages relevant to the current phase."""
        # For simplicity, return recent messages
        # In production, filter by phase
        messages = []
        for msg in session.messages[-10:]:  # Last 10 messages
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        return messages

    async def _check_phase_completion(self, session: DiagnosisSession) -> None:
        """Check if current phase is complete and advance if needed."""
        # This would involve more sophisticated logic in production
        # For now, phases are advanced manually through the conversation
        pass

    async def advance_phase(self, session_id: str) -> tuple[bool, str]:
        """
        Manually advance to the next phase.

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (success, message)
        """
        if session_id not in self.sessions:
            return False, "セッションが見つかりません。"

        session = self.sessions[session_id]
        success = session.advance_phase()

        if success:
            # Update todo middleware
            if session_id in self.todo_middlewares:
                self.todo_middlewares[session_id].advance_phase()

            await self._save_session(session)
            return True, f"Phase {session.current_phase.value} に進みました。"
        else:
            return False, "最終フェーズです。診断が完了しました。"

    async def _save_session(self, session: DiagnosisSession) -> None:
        """Save session to storage."""
        session_data = session.model_dump(mode="json")
        await self.file_backend.write_file(
            f"/sessions/{session.session_id}/session.json",
            json.dumps(session_data, ensure_ascii=False, indent=2),
        )

    async def get_session_status(self, session_id: str) -> dict:
        """Get session status."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}

        session = self.sessions[session_id]
        todo_status = None
        if session_id in self.todo_middlewares:
            todo_status = self.todo_middlewares[session_id].get_status()

        phases_completed = len([p for p in session.phases if p.status == PhaseStatus.COMPLETED])

        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "current_phase": session.current_phase.value,
            "phase_name": session.get_current_phase_info().name if session.get_current_phase_info() else "",
            "phases_completed": phases_completed,
            "total_phases": len(session.phases),
            "progress_percentage": (phases_completed / len(session.phases) * 100) if session.phases else 0,
            "is_complete": session.is_complete,
            "todos": todo_status,
        }

    async def get_session_result(self, session_id: str) -> dict:
        """Get complete session result."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}

        session = self.sessions[session_id]
        assessment = self.assessment_data.get(session_id, {})

        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "is_complete": session.is_complete,
            "foundation_assessment": assessment.get("foundation"),
            "domain_assessment": assessment.get("domain"),
            "technical_assessment": assessment.get("technical"),
            "architecture_assessment": assessment.get("architecture"),
            "roadmap": assessment.get("roadmap"),
        }

    def get_todo_display(self, session_id: str) -> str:
        """Get formatted todo display for a session."""
        if session_id not in self.todo_middlewares:
            return "セッションが見つかりません。"
        return self.todo_middlewares[session_id].format_for_display()

