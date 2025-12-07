"""API dependencies for authentication and session management."""

import json
import re
from typing import Optional
from uuid import UUID

from fastapi import Cookie, Header, HTTPException, status

from app.config import get_settings


def validate_session_id_format(session_id: str) -> str:
    """Validate that session ID is in UUID format.

    Args:
        session_id: Session ID to validate.

    Returns:
        Validated session ID string.

    Raises:
        HTTPException: If session ID is not in valid UUID format.
    """
    # UUID format: 8-4-4-4-12 hexadecimal characters
    # Example: a0cbbfc4-0635-41c2-9dba-9ed7d708fd1e
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

    if not re.match(uuid_pattern, session_id.lower()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションIDの形式が無効です。ログインが必要です。",
        )

    # Also try to parse as UUID to ensure it's valid
    try:
        UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションIDの形式が無効です。ログインが必要です。",
        )

    return session_id


def get_session_id(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
) -> str:
    """Get session ID from cookie or header and validate format.

    Args:
        session_id: Session ID from cookie.
        x_session_id: Session ID from header.

    Returns:
        Validated session ID string.

    Raises:
        HTTPException: If session ID is not provided or invalid format.
    """
    sid = None
    if session_id:
        sid = session_id
    elif x_session_id:
        sid = x_session_id

    if not sid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションIDが提供されていません。ログインが必要です。",
        )

    # Validate UUID format
    return validate_session_id_format(sid)


def verify_session(session_id: str) -> dict:
    """Verify that a session exists and is valid.

    Args:
        session_id: Session ID to verify.

    Returns:
        Session data dictionary.

    Raises:
        HTTPException: If session does not exist or is invalid.
    """
    settings = get_settings()
    sessions_dir = settings.sessions_dir

    # Look for session file in various possible locations
    # Format: {session_id}/session.json or {session_id}.json
    session_file = sessions_dir / session_id / "session.json"
    if not session_file.exists():
        session_file = sessions_dir / f"{session_id}.json"
    if not session_file.exists():
        # Also check in eng_career_diagnosis subdirectory
        session_file = sessions_dir / "eng_career_diagnosis" / f"{session_id}.json"
    if not session_file.exists():
        # Check in diagnosis subdirectory
        session_file = sessions_dir / "diagnosis" / f"{session_id}.json"

    if not session_file.exists():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが見つかりません。ログインが必要です。",
        )

    try:
        with open(session_file, encoding="utf-8") as f:
            session_data = json.load(f)
        return session_data
    except (json.JSONDecodeError, IOError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"セッションデータの読み込みに失敗しました: {str(e)}",
        )


def require_session(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
) -> dict:
    """Dependency to require a valid session.

    This dependency can be used in FastAPI route handlers to ensure
    the user has a valid session.

    Args:
        session_id: Session ID from cookie.
        x_session_id: Session ID from header.

    Returns:
        Session data dictionary.

    Raises:
        HTTPException: If session is not provided or invalid.
    """
    sid = get_session_id(session_id=session_id, x_session_id=x_session_id)
    return verify_session(sid)
