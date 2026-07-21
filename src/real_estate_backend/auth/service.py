from sqlalchemy.orm import Session
from sqlalchemy import select
from real_estate_backend.users.model import User
from real_estate_backend.auth.schema import SignupRequest, LoginRequest, TokenResponse
from real_estate_backend.core.security import hash_password, verify_password, create_access_token
from real_estate_backend.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from real_estate_backend.core.enums import UserRole
from real_estate_backend.core.logging import log_call


@log_call
def signup(db: Session, data: SignupRequest) -> User:
    normalized_email = str(data.email).lower()

    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if existing_user:
        raise EmailAlreadyExistsError(normalized_email)

    user = User(
        email=normalized_email,
        password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.USER,
    )

    db.add(user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user

@log_call
def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == data.email))

    # Check user exists AND password matches
    # Both checks done together — don't reveal which one failed
    if not user or not verify_password(data.password, user.password):
        raise InvalidCredentialsError()

    token = create_access_token({
        "user_id": user.id,
        "role": user.role.value,
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
    )