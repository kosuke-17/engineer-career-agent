"""Diagnosis-related models for Learning Path Agent."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DiagnosisPhase(str, Enum):
    """Diagnosis phases enum."""

    FOUNDATION = "foundation"  # Phase 1: 基礎スキル診断
    DOMAIN = "domain"  # Phase 2: 専攻領域選定
    TECHNICAL = "technical"  # Phase 3: 詳細技術診断
    ARCHITECTURE = "architecture"  # Phase 4: アーキテクチャ適性
    ROADMAP = "roadmap"  # Phase 5: 学習ロードマップ生成


class PhaseStatus(str, Enum):
    """Phase status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class DiagnosisPhaseInfo(BaseModel):
    """Information about a diagnosis phase."""

    phase: DiagnosisPhase
    name: str
    description: str
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None


class Message(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)


class DiagnosisSession(BaseModel):
    """Diagnosis session model."""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    current_phase: DiagnosisPhase = Field(default=DiagnosisPhase.FOUNDATION)
    phases: list[DiagnosisPhaseInfo] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    is_complete: bool = Field(default=False)
    metadata: dict = Field(default_factory=dict)

    def model_post_init(self, __context) -> None:
        """Initialize phases if empty."""
        if not self.phases:
            self.phases = [
                DiagnosisPhaseInfo(
                    phase=DiagnosisPhase.FOUNDATION,
                    name="基礎スキル診断",
                    description="プログラミング基礎、アルゴリズム、データ構造を診断",
                ),
                DiagnosisPhaseInfo(
                    phase=DiagnosisPhase.DOMAIN,
                    name="専攻領域選定",
                    description="フロントエンド/バックエンド/インフラなど適性を判定",
                ),
                DiagnosisPhaseInfo(
                    phase=DiagnosisPhase.TECHNICAL,
                    name="詳細技術診断",
                    description="選定領域の具体的な技術スタック適性を評価",
                ),
                DiagnosisPhaseInfo(
                    phase=DiagnosisPhase.ARCHITECTURE,
                    name="アーキテクチャ適性",
                    description="システム設計・アーキテクチャ思考能力を診断",
                ),
                DiagnosisPhaseInfo(
                    phase=DiagnosisPhase.ROADMAP,
                    name="学習ロードマップ生成",
                    description="全ての診断結果から最適な学習パスを生成",
                ),
            ]

    def get_current_phase_info(self) -> Optional[DiagnosisPhaseInfo]:
        """Get current phase information."""
        for phase_info in self.phases:
            if phase_info.phase == self.current_phase:
                return phase_info
        return None

    def advance_phase(self) -> bool:
        """Advance to the next phase."""
        phase_order = list(DiagnosisPhase)
        current_idx = phase_order.index(self.current_phase)

        if current_idx >= len(phase_order) - 1:
            self.is_complete = True
            return False

        # Mark current phase as completed
        current_phase_info = self.get_current_phase_info()
        if current_phase_info:
            current_phase_info.status = PhaseStatus.COMPLETED
            current_phase_info.completed_at = datetime.now()

        # Move to next phase
        self.current_phase = phase_order[current_idx + 1]
        next_phase_info = self.get_current_phase_info()
        if next_phase_info:
            next_phase_info.status = PhaseStatus.IN_PROGRESS
            next_phase_info.started_at = datetime.now()

        self.updated_at = datetime.now()
        return True

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.now()


class DiagnosisResult(BaseModel):
    """Final diagnosis result model."""

    session_id: str
    user_id: str
    completed_at: datetime = Field(default_factory=datetime.now)
    foundation_score: float = Field(..., ge=0, le=10)
    domain_scores: dict[str, float] = Field(default_factory=dict)
    recommended_domain: str
    technical_skills: dict[str, float] = Field(default_factory=dict)
    architecture_score: float = Field(..., ge=0, le=10)
    roadmap: dict = Field(default_factory=dict)
    summary: str = Field(default="")
    recommendations: list[str] = Field(default_factory=list)


# Request/Response models for API


class StartDiagnosisRequest(BaseModel):
    """Request to start a new diagnosis session."""

    user_id: str = Field(..., description="User identifier")
    initial_message: Optional[str] = Field(
        default=None, description="Optional initial message from user"
    )


class SendMessageRequest(BaseModel):
    """Request to send a message in diagnosis session."""

    message: str = Field(..., description="User's message")


class DiagnosisStatusResponse(BaseModel):
    """Response for diagnosis status."""

    session_id: str
    current_phase: DiagnosisPhase
    phase_name: str
    phase_description: str
    phases_completed: int
    total_phases: int
    is_complete: bool
    progress_percentage: float


class DiagnosisMessageResponse(BaseModel):
    """Response for diagnosis message."""

    session_id: str
    assistant_message: str
    current_phase: DiagnosisPhase
    phase_name: str
    is_complete: bool
    todos: Optional[list[dict]] = None
