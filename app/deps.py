from pathlib import Path
from typing import Callable
from fastapi import Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app.models.users import Role, User
from app.security import decode_access_token

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


class NotAuthenticatedException(Exception):
    """Raised when a user is missing or has an invalid/expired session cookie."""


def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise NotAuthenticatedException()

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise NotAuthenticatedException()

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise NotAuthenticatedException()

    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise NotAuthenticatedException()

    return user


def require_role(*allowed_roles: Role | str) -> Callable[[Request, User], User]:
    """Dependency factory that verifies the logged-in user holds one of the allowed roles."""
    normalized_roles = {
        r.value if isinstance(r, Role) else str(r) for r in allowed_roles
    }

    def _role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_role = (
            current_user.role.value
            if isinstance(current_user.role, Role)
            else str(current_user.role)
        )
        if user_role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this page.",
            )
        return current_user

    return _role_checker