"""Diagnosis session entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from ..value_objects import Phase, PhaseStatus


@dataclass
class PhaseInfo:
    """Information about a diagnosis phase."""

    phase: Phase
    status: PhaseStatus = PhaseStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict[str, Any]] = None

    def start(self) -> None:
        """Mark phase as started."""
        self.status = PhaseStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self, result: Optional[dict[str, Any]] = None) -> None:
        """Mark phase as completed with optional result."""
        self.status = PhaseStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def skip(self) -> None:
        """Mark phase as skipped."""
        self.status = PhaseStatus.SKIPPED
        self.completed_at = datetime.now()


@dataclass
class Message:
    """A message in the diagnosis conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    phase: Optional[Phase] = None


@dataclass
class DiagnosisPhase:
    """Alias for PhaseInfo for backwards compatibility."""

    phase: Phase
    status: PhaseStatus = PhaseStatus.PENDING
    result: Optional[dict[str, Any]] = None


@dataclass
class DiagnosisSession:
    """Entity representing a diagnosis session."""

    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    current_phase: Phase = Phase.FOUNDATION
    phases: dict[str, PhaseInfo] = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Initialize phases if not provided."""
        if not self.phases:
            self._initialize_phases()

    def _initialize_phases(self) -> None:
        """Initialize all phases with pending status."""
        for phase in Phase:
            self.phases[phase.value] = PhaseInfo(phase=phase)

    @classmethod
    def create(cls, user_id: Optional[str] = None) -> "DiagnosisSession":
        """Factory method to create a new diagnosis session."""
        session = cls(user_id=user_id)
        # Start the first phase
        session.start_phase(Phase.FOUNDATION)
        return session

    def start_phase(self, phase: Phase) -> None:
        """Start a specific phase."""
        if phase.value in self.phases:
            self.phases[phase.value].start()
            self.current_phase = phase
            self.updated_at = datetime.now()

    def complete_current_phase(self, result: Optional[dict[str, Any]] = None) -> None:
        """Complete the current phase and move to the next one."""
        current = self.phases.get(self.current_phase.value)
        if current:
            current.complete(result)

        next_phase = self.current_phase.next_phase()
        if next_phase:
            self.start_phase(next_phase)
        else:
            self.is_completed = True

        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        message = Message(role=role, content=content, phase=self.current_phase)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_phase_info(self, phase: Phase) -> Optional[PhaseInfo]:
        """Get information about a specific phase."""
        return self.phases.get(phase.value)

    def get_current_phase_info(self) -> Optional[PhaseInfo]:
        """Get information about the current phase."""
        return self.get_phase_info(self.current_phase)

    def get_completed_phases(self) -> list[PhaseInfo]:
        """Get all completed phases."""
        return [info for info in self.phases.values() if info.status == PhaseStatus.COMPLETED]

    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        total = len(self.phases)
        completed = len(self.get_completed_phases())
        return (completed / total) * 100 if total > 0 else 0

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get conversation history in a simple format."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "current_phase": self.current_phase.value,
            "phases": {
                name: {
                    "phase": info.phase.value,
                    "status": info.status.value,
                    "started_at": info.started_at.isoformat() if info.started_at else None,
                    "completed_at": info.completed_at.isoformat() if info.completed_at else None,
                    "result": info.result,
                }
                for name, info in self.phases.items()
            },
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "phase": msg.phase.value if msg.phase else None,
                }
                for msg in self.messages
            ],
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
