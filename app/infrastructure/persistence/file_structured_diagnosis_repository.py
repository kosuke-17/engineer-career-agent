"""File-based structured diagnosis repository implementation."""

import json
from pathlib import Path
from typing import Optional

from app.domain.entities import StructuredDiagnosisSession
from app.domain.repositories import StructuredDiagnosisRepository


class FileStructuredDiagnosisRepository(StructuredDiagnosisRepository):
    """File-based implementation of StructuredDiagnosisRepository."""

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

    async def save(self, session: StructuredDiagnosisSession) -> None:
        """Save a diagnosis session."""
        file_path = self._get_file_path(session.id)
        data = session.to_dict()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def find_by_id(self, session_id: str) -> Optional[StructuredDiagnosisSession]:
        """Find a session by ID."""
        file_path = self._get_file_path(session_id)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return StructuredDiagnosisSession.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    async def find_by_user_id(self, user_id: str) -> list[StructuredDiagnosisSession]:
        """Find all sessions for a user."""
        sessions = []
        for file_path in self.base_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("user_id") == user_id:
                    session = StructuredDiagnosisSession.from_dict(data)
                    sessions.append(session)
            except (json.JSONDecodeError, KeyError):
                continue
        return sessions

    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

