"""File-based diagnosis repository implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.domain.entities import DiagnosisSession, Message, PhaseInfo
from app.domain.repositories import DiagnosisRepository
from app.domain.value_objects import Phase, PhaseStatus


class FileDiagnosisRepository(DiagnosisRepository):
    """File-based implementation of DiagnosisRepository."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        # パストラバーサル対策
        safe_id = session_id.replace("/", "_").replace("\\", "_").replace("..", "_")
        path = (self.base_path / f"{safe_id}.json").resolve()
        if not str(path).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid session ID: path traversal detected")
        return path

    async def find_by_id(self, session_id: str) -> Optional[DiagnosisSession]:
        """Find a diagnosis session by ID."""
        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._dict_to_session(data)
        except (json.JSONDecodeError, KeyError):
            return None

    async def find_by_user_id(self, user_id: str) -> list[DiagnosisSession]:
        """Find all diagnosis sessions for a user."""
        sessions = []
        for file_path in self.base_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("user_id") == user_id:
                    session = self._dict_to_session(data)
                    sessions.append(session)
            except (json.JSONDecodeError, KeyError):
                continue
        return sessions

    async def find_active_by_user_id(
        self, user_id: str
    ) -> Optional[DiagnosisSession]:
        """Find the active (incomplete) diagnosis session for a user."""
        sessions = await self.find_by_user_id(user_id)
        for session in sessions:
            if not session.is_completed:
                return session
        return None

    async def save(self, session: DiagnosisSession) -> None:
        """Save a diagnosis session."""
        file_path = self._get_file_path(session.id)
        data = self._session_to_dict(session)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def delete(self, session_id: str) -> bool:
        """Delete a diagnosis session by ID."""
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def exists(self, session_id: str) -> bool:
        """Check if a diagnosis session exists."""
        file_path = self._get_file_path(session_id)
        return file_path.exists()

    def _session_to_dict(self, session: DiagnosisSession) -> dict:
        """Convert session entity to dictionary."""
        return {
            "id": session.id,
            "user_id": session.user_id,
            "current_phase": session.current_phase.value,
            "phases": {
                name: {
                    "phase": info.phase.value,
                    "status": info.status.value,
                    "started_at": info.started_at.isoformat() if info.started_at else None,
                    "completed_at": info.completed_at.isoformat() if info.completed_at else None,
                    "result": info.result,
                }
                for name, info in session.phases.items()
            },
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "phase": msg.phase.value if msg.phase else None,
                }
                for msg in session.messages
            ],
            "is_completed": session.is_completed,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }

    def _dict_to_session(self, data: dict) -> DiagnosisSession:
        """Convert dictionary to session entity."""
        # Parse phases
        phases = {}
        for name, info_data in data.get("phases", {}).items():
            started_at = None
            completed_at = None
            if info_data.get("started_at"):
                try:
                    started_at = datetime.fromisoformat(info_data["started_at"])
                except ValueError:
                    pass
            if info_data.get("completed_at"):
                try:
                    completed_at = datetime.fromisoformat(info_data["completed_at"])
                except ValueError:
                    pass

            phases[name] = PhaseInfo(
                phase=Phase(info_data["phase"]),
                status=PhaseStatus(info_data["status"]),
                started_at=started_at,
                completed_at=completed_at,
                result=info_data.get("result"),
            )

        # Parse messages
        messages = []
        for msg_data in data.get("messages", []):
            timestamp = datetime.now()
            if msg_data.get("timestamp"):
                try:
                    timestamp = datetime.fromisoformat(msg_data["timestamp"])
                except ValueError:
                    pass

            phase = None
            if msg_data.get("phase"):
                try:
                    phase = Phase(msg_data["phase"])
                except ValueError:
                    pass

            messages.append(
                Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=timestamp,
                    phase=phase,
                )
            )

        # Parse timestamps
        created_at = datetime.now()
        updated_at = datetime.now()
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                pass
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except ValueError:
                pass

        session = DiagnosisSession(
            id=data["id"],
            user_id=data.get("user_id"),
            current_phase=Phase(data["current_phase"]),
            phases=phases,
            messages=messages,
            is_completed=data.get("is_completed", False),
            created_at=created_at,
            updated_at=updated_at,
        )
        return session

