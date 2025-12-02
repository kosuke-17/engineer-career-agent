"""Structured diagnosis session entity for v2 diagnosis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class StructuredDiagnosisPhase(str, Enum):
    """Phases for the structured diagnosis flow."""

    DOMAIN_SELECTION = "domain_selection"
    GOAL_SELECTION = "goal_selection"
    COMMON_QUESTIONS = "common_questions"
    DOMAIN_QUESTIONS = "domain_questions"
    ROADMAP_GENERATION = "roadmap_generation"
    COMPLETED = "completed"

    @property
    def display_name(self) -> str:
        """Get display name for the phase."""
        names = {
            StructuredDiagnosisPhase.DOMAIN_SELECTION: "領域選択",
            StructuredDiagnosisPhase.GOAL_SELECTION: "ゴール選択",
            StructuredDiagnosisPhase.COMMON_QUESTIONS: "共通質問",
            StructuredDiagnosisPhase.DOMAIN_QUESTIONS: "専門質問",
            StructuredDiagnosisPhase.ROADMAP_GENERATION: "ロードマップ生成",
            StructuredDiagnosisPhase.COMPLETED: "完了",
        }
        return names.get(self, self.value)

    @property
    def order(self) -> int:
        """Get the order of the phase."""
        order_map = {
            StructuredDiagnosisPhase.DOMAIN_SELECTION: 1,
            StructuredDiagnosisPhase.GOAL_SELECTION: 2,
            StructuredDiagnosisPhase.COMMON_QUESTIONS: 3,
            StructuredDiagnosisPhase.DOMAIN_QUESTIONS: 4,
            StructuredDiagnosisPhase.ROADMAP_GENERATION: 5,
            StructuredDiagnosisPhase.COMPLETED: 6,
        }
        return order_map.get(self, 0)

    def next_phase(self) -> Optional["StructuredDiagnosisPhase"]:
        """Get the next phase in sequence."""
        phase_order = [
            StructuredDiagnosisPhase.DOMAIN_SELECTION,
            StructuredDiagnosisPhase.GOAL_SELECTION,
            StructuredDiagnosisPhase.COMMON_QUESTIONS,
            StructuredDiagnosisPhase.DOMAIN_QUESTIONS,
            StructuredDiagnosisPhase.ROADMAP_GENERATION,
            StructuredDiagnosisPhase.COMPLETED,
        ]
        try:
            current_idx = phase_order.index(self)
            if current_idx < len(phase_order) - 1:
                return phase_order[current_idx + 1]
        except ValueError:
            pass
        return None


@dataclass
class QuestionAnswer:
    """A single question-answer pair."""

    question_id: str
    question_text: str
    selected_options: list[str] = field(default_factory=list)
    selected_labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "selected_options": self.selected_options,
            "selected_labels": self.selected_labels,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuestionAnswer":
        """Create from dictionary."""
        return cls(
            question_id=data.get("question_id", ""),
            question_text=data.get("question_text", ""),
            selected_options=data.get("selected_options", []),
            selected_labels=data.get("selected_labels", []),
        )


@dataclass
class StructuredDiagnosisSession:
    """Entity representing a structured diagnosis session (v2)."""

    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None

    # Current phase
    current_phase: StructuredDiagnosisPhase = StructuredDiagnosisPhase.DOMAIN_SELECTION

    # Selections
    selected_domain: Optional[str] = None
    selected_goal_id: Optional[str] = None
    selected_goal_label: Optional[str] = None

    # Answers
    common_answers: list[QuestionAnswer] = field(default_factory=list)
    domain_answers: list[QuestionAnswer] = field(default_factory=list)

    # Generated roadmap
    roadmap: Optional[dict[str, Any]] = None

    # Timestamps
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(cls, user_id: Optional[str] = None) -> "StructuredDiagnosisSession":
        """Factory method to create a new session."""
        return cls(user_id=user_id)

    def select_domain(self, domain: str) -> None:
        """Select a domain and advance to goal selection."""
        self.selected_domain = domain
        self.current_phase = StructuredDiagnosisPhase.GOAL_SELECTION
        self.updated_at = datetime.now()

    def select_goal(self, goal_id: str, goal_label: str) -> None:
        """Select a goal and advance to common questions."""
        self.selected_goal_id = goal_id
        self.selected_goal_label = goal_label
        self.current_phase = StructuredDiagnosisPhase.COMMON_QUESTIONS
        self.updated_at = datetime.now()

    def add_common_answers(self, answers: list[QuestionAnswer]) -> None:
        """Add answers to common questions."""
        self.common_answers.extend(answers)
        self.updated_at = datetime.now()

    def complete_common_questions(self) -> None:
        """Complete common questions and move to domain questions."""
        self.current_phase = StructuredDiagnosisPhase.DOMAIN_QUESTIONS
        self.updated_at = datetime.now()

    def add_domain_answers(self, answers: list[QuestionAnswer]) -> None:
        """Add answers to domain-specific questions."""
        self.domain_answers.extend(answers)
        self.updated_at = datetime.now()

    def complete_domain_questions(self) -> None:
        """Complete domain questions and move to roadmap generation."""
        self.current_phase = StructuredDiagnosisPhase.ROADMAP_GENERATION
        self.updated_at = datetime.now()

    def set_roadmap(self, roadmap: dict[str, Any]) -> None:
        """Set the generated roadmap and mark as completed."""
        self.roadmap = roadmap
        self.current_phase = StructuredDiagnosisPhase.COMPLETED
        self.is_completed = True
        self.updated_at = datetime.now()

    def get_all_answers(self) -> list[QuestionAnswer]:
        """Get all answers (common + domain)."""
        return self.common_answers + self.domain_answers

    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        phase_weights = {
            StructuredDiagnosisPhase.DOMAIN_SELECTION: 0,
            StructuredDiagnosisPhase.GOAL_SELECTION: 20,
            StructuredDiagnosisPhase.COMMON_QUESTIONS: 40,
            StructuredDiagnosisPhase.DOMAIN_QUESTIONS: 60,
            StructuredDiagnosisPhase.ROADMAP_GENERATION: 80,
            StructuredDiagnosisPhase.COMPLETED: 100,
        }
        return phase_weights.get(self.current_phase, 0)

    def get_context_for_roadmap(self) -> dict[str, Any]:
        """Get full context for roadmap generation."""
        return {
            "domain": self.selected_domain,
            "goal": {
                "id": self.selected_goal_id,
                "label": self.selected_goal_label,
            },
            "common_answers": [a.to_dict() for a in self.common_answers],
            "domain_answers": [a.to_dict() for a in self.domain_answers],
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "current_phase": self.current_phase.value,
            "selected_domain": self.selected_domain,
            "selected_goal_id": self.selected_goal_id,
            "selected_goal_label": self.selected_goal_label,
            "common_answers": [a.to_dict() for a in self.common_answers],
            "domain_answers": [a.to_dict() for a in self.domain_answers],
            "roadmap": self.roadmap,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredDiagnosisSession":
        """Create session from dictionary."""
        session = cls(
            id=data.get("id", str(uuid4())),
            user_id=data.get("user_id"),
            current_phase=StructuredDiagnosisPhase(data.get("current_phase", "domain_selection")),
            selected_domain=data.get("selected_domain"),
            selected_goal_id=data.get("selected_goal_id"),
            selected_goal_label=data.get("selected_goal_label"),
            roadmap=data.get("roadmap"),
            is_completed=data.get("is_completed", False),
        )

        # Parse timestamps
        if "created_at" in data:
            session.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            session.updated_at = datetime.fromisoformat(data["updated_at"])

        # Parse answers
        for answer_data in data.get("common_answers", []):
            session.common_answers.append(QuestionAnswer.from_dict(answer_data))
        for answer_data in data.get("domain_answers", []):
            session.domain_answers.append(QuestionAnswer.from_dict(answer_data))

        return session

