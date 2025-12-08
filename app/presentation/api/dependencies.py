"""API dependencies for authentication and session management."""

import re
from typing import Optional
from uuid import UUID

from fastapi import Cookie, Header, HTTPException, status


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


def verify_session(
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


def require_session(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id"),
) -> dict:
    """Dependency to require a valid session.

    This dependency can be used in FastAPI route handlers to ensure
    the user has a valid session. It validates that the session ID
    is in UUID format.

    Args:
        session_id: Session ID from cookie.
        x_session_id: Session ID from header.

    Returns:
        Empty dict (session validation passed).

    Raises:
        HTTPException: If session is not provided or invalid format.
    """
    # verify_session calls validate_session_id_format internally
    # This will raise HTTPException if session ID is invalid
    verify_session(session_id=session_id, x_session_id=x_session_id)
    # Return empty dict to indicate session is valid
    return {}
