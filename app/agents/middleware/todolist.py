"""TodoList Middleware for managing diagnosis phases."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    """Todo item status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class TodoItem(BaseModel):
    """Individual todo item."""

    id: str = Field(..., description="Unique identifier")
    phase: int = Field(..., ge=1, le=5, description="Phase number")
    name: str = Field(..., description="Todo name")
    description: str = Field(default="", description="Detailed description")
    status: TodoStatus = Field(default=TodoStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    notes: str = Field(default="")


class DiagnosisTodoList(BaseModel):
    """Todo list for diagnosis phases."""

    session_id: str
    todos: list[TodoItem] = Field(default_factory=list)
    current_phase: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def model_post_init(self, __context) -> None:
        """Initialize default todos if empty."""
        if not self.todos:
            self.todos = self._create_default_todos()

    def _create_default_todos(self) -> list[TodoItem]:
        """Create default diagnosis phase todos."""
        phases = [
            {
                "phase": 1,
                "name": "基礎スキル診断",
                "description": "プログラミング基礎、アルゴリズム、データ構造を診断",
            },
            {
                "phase": 2,
                "name": "専攻領域選定",
                "description": "フロントエンド/バックエンド/インフラなど適性を判定",
            },
            {
                "phase": 3,
                "name": "詳細技術診断",
                "description": "選定領域の具体的な技術スタック適性を評価",
            },
            {
                "phase": 4,
                "name": "アーキテクチャ適性",
                "description": "システム設計・アーキテクチャ思考能力を診断",
            },
            {
                "phase": 5,
                "name": "学習ロードマップ生成",
                "description": "全ての診断結果から最適な学習パスを生成",
            },
        ]

        todos = []
        for p in phases:
            todos.append(
                TodoItem(
                    id=f"phase_{p['phase']}",
                    phase=p["phase"],
                    name=p["name"],
                    description=p["description"],
                    status=TodoStatus.IN_PROGRESS if p["phase"] == 1 else TodoStatus.PENDING,
                )
            )
        return todos

    def get_current_todo(self) -> Optional[TodoItem]:
        """Get the current in-progress todo."""
        for todo in self.todos:
            if todo.status == TodoStatus.IN_PROGRESS:
                return todo
        return None

    def get_todo_by_phase(self, phase: int) -> Optional[TodoItem]:
        """Get todo by phase number."""
        for todo in self.todos:
            if todo.phase == phase:
                return todo
        return None

    def get_completed_todos(self) -> list[TodoItem]:
        """Get all completed todos."""
        return [t for t in self.todos if t.status == TodoStatus.COMPLETED]

    def get_pending_todos(self) -> list[TodoItem]:
        """Get all pending todos."""
        return [t for t in self.todos if t.status == TodoStatus.PENDING]


class TodoListMiddleware:
    """Middleware for managing diagnosis todo list."""

    def __init__(self, session_id: str):
        self.todo_list = DiagnosisTodoList(session_id=session_id)

    def get_system_prompt_addition(self) -> str:
        """Get system prompt addition for todo management."""
        return """
あなたは学習パスアドバイザーです。以下の診断フェーズを順番に実施してください：

## 診断フェーズ
1. 基礎スキル診断 - プログラミング基礎、アルゴリズム、データ構造を診断
2. 専攻領域選定 - フロントエンド/バックエンド/インフラなど適性を判定
3. 詳細技術診断 - 選定領域の具体的な技術スタック適性を評価
4. アーキテクチャ適性 - システム設計・アーキテクチャ思考能力を診断
5. 学習ロードマップ生成 - 全ての診断結果から最適な学習パスを生成

## 進行ルール
- write_todos ツールを使って診断の進捗を管理してください
- 各フェーズ完了時にステータスを更新してください
- 前のフェーズの結果に基づいて次のフェーズを適応させてください
- 徹底的に質問し、学習者を深く理解してください
"""

    def write_todos(
        self,
        todos: list[dict],
        merge: bool = True,
    ) -> dict:
        """
        Write or update todos.

        Args:
            todos: List of todo items to write/update
            merge: If True, merge with existing todos; if False, replace

        Returns:
            Updated todo list status
        """
        if not merge:
            # Replace all todos
            self.todo_list.todos = []

        for todo_data in todos:
            todo_id = todo_data.get("id")
            existing = None

            # Find existing todo
            for i, t in enumerate(self.todo_list.todos):
                if t.id == todo_id:
                    existing = (i, t)
                    break

            if existing:
                idx, existing_todo = existing
                # Update existing todo
                if "status" in todo_data:
                    new_status = TodoStatus(todo_data["status"])
                    existing_todo.status = new_status
                    if new_status == TodoStatus.COMPLETED:
                        existing_todo.completed_at = datetime.now()
                if "name" in todo_data:
                    existing_todo.name = todo_data["name"]
                if "description" in todo_data:
                    existing_todo.description = todo_data["description"]
                if "notes" in todo_data:
                    existing_todo.notes = todo_data["notes"]
                existing_todo.updated_at = datetime.now()
            else:
                # Add new todo
                new_todo = TodoItem(
                    id=todo_id or f"custom_{len(self.todo_list.todos)}",
                    phase=todo_data.get("phase", 0),
                    name=todo_data.get("name", ""),
                    description=todo_data.get("description", ""),
                    status=TodoStatus(todo_data.get("status", "pending")),
                    notes=todo_data.get("notes", ""),
                )
                self.todo_list.todos.append(new_todo)

        self.todo_list.updated_at = datetime.now()

        return self.get_status()

    def edit_todo(
        self,
        todo_id: str,
        status: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Edit a specific todo item.

        Args:
            todo_id: ID of the todo to edit
            status: New status (pending, in_progress, completed, skipped)
            name: New name
            description: New description
            notes: Additional notes

        Returns:
            Updated todo status
        """
        for todo in self.todo_list.todos:
            if todo.id == todo_id:
                if status:
                    todo.status = TodoStatus(status)
                    if TodoStatus(status) == TodoStatus.COMPLETED:
                        todo.completed_at = datetime.now()
                if name:
                    todo.name = name
                if description:
                    todo.description = description
                if notes is not None:
                    todo.notes = notes
                todo.updated_at = datetime.now()
                break

        self.todo_list.updated_at = datetime.now()
        return self.get_status()

    def advance_phase(self) -> dict:
        """Mark current phase as completed and advance to next."""
        current = self.get_current_todo()
        if current:
            current.status = TodoStatus.COMPLETED
            current.completed_at = datetime.now()
            current.updated_at = datetime.now()

            # Find and start next phase
            next_phase = current.phase + 1
            for todo in self.todo_list.todos:
                if todo.phase == next_phase:
                    todo.status = TodoStatus.IN_PROGRESS
                    todo.updated_at = datetime.now()
                    self.todo_list.current_phase = next_phase
                    break

        self.todo_list.updated_at = datetime.now()
        return self.get_status()

    def get_current_todo(self) -> Optional[TodoItem]:
        """Get the current in-progress todo."""
        return self.todo_list.get_current_todo()

    def get_status(self) -> dict:
        """Get current todo list status."""
        completed = len(self.todo_list.get_completed_todos())
        total = len(self.todo_list.todos)

        return {
            "session_id": self.todo_list.session_id,
            "current_phase": self.todo_list.current_phase,
            "progress": f"{completed}/{total}",
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "todos": [
                {
                    "id": t.id,
                    "phase": t.phase,
                    "name": t.name,
                    "description": t.description,
                    "status": t.status.value,
                    "notes": t.notes,
                }
                for t in self.todo_list.todos
            ],
        }

    def format_for_display(self) -> str:
        """Format todo list for display in chat."""
        lines = ["## 診断進捗状況\n"]

        status_icons = {
            TodoStatus.PENDING: "⏳",
            TodoStatus.IN_PROGRESS: "🔄",
            TodoStatus.COMPLETED: "✅",
            TodoStatus.SKIPPED: "⏭️",
        }

        for todo in self.todo_list.todos:
            icon = status_icons.get(todo.status, "❓")
            line = f"{icon} **Phase {todo.phase}: {todo.name}**"
            if todo.status == TodoStatus.IN_PROGRESS:
                line += " (進行中)"
            elif todo.status == TodoStatus.COMPLETED:
                line += " (完了)"
            lines.append(line)
            if todo.notes:
                lines.append(f"   📝 {todo.notes}")

        completed = len(self.todo_list.get_completed_todos())
        total = len(self.todo_list.todos)
        lines.append(f"\n**進捗: {completed}/{total} ({completed / total * 100:.0f}%)**")

        return "\n".join(lines)
