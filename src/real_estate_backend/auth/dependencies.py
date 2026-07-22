from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError
from real_estate_backend.core.enums import UserRole
from real_estate_backend.core.database import get_db
from real_estate_backend.core.security import decode_access_token
from real_estate_backend.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    UserNotFoundError,
    PermissionDeniedError,
    LeadNotFoundError,
)
from real_estate_backend.users.model import User
from real_estate_backend.leads.model import Lead

# Tells FastAPI where to find the token
# tokenUrl is what Swagger uses for the Authorize button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and verifies JWT token from Authorization header.
    Returns the user object if valid.
    Raises 401 if anything is wrong.
    """
    if token is None:
        raise InvalidTokenError()
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise InvalidTokenError()

    except ExpiredSignatureError:
        raise TokenExpiredError()

    except JWTError:
        raise InvalidTokenError()

    # Confirm user still exists in DB
    user = db.get(User, user_id)
    if not user:
        raise UserNotFoundError(user_id)

    if not user.is_active:
        raise InvalidTokenError()

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Only admin passes. Agent and customer get 403."""
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedError("only admins can perform this action")
    return current_user


def require_agent_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Admin and agent pass. Customer gets 403."""
    if current_user.role not in {UserRole.ADMIN, UserRole.AGENT}:
        raise PermissionDeniedError("only agents and admins can perform this action")
    return current_user


def require_any_authenticated(
    current_user: User = Depends(get_current_user),
) -> User:
    """All three roles pass — just needs valid token."""
    return current_user


def require_lead_ownership(
    lead_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Lead:
    """
    Admin    → always passes
    Agent    → passes only if lead.agent_id == current_user.id
    Customer → always fails
    """
    lead = db.get(Lead, lead_id)
    if not lead:
        raise LeadNotFoundError(lead_id)

    if current_user.role == UserRole.ADMIN:
        return lead

    if current_user.role == UserRole.USER:
        raise PermissionDeniedError(
            "users cannot access leads"
        )

    if lead.agent_id != current_user.id:
        raise PermissionDeniedError("you can only access leads assigned to you")

    return lead


def require_agent(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.AGENT:
        raise PermissionDeniedError(
            "agent access required"
        )

    return current_user