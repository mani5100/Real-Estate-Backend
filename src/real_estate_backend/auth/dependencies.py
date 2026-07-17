from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError

from real_estate_backend.core.database import get_db
from real_estate_backend.core.security import decode_access_token
from real_estate_backend.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    UserNotFoundError,
)
from real_estate_backend.users.model import User

# Tells FastAPI where to find the token
# tokenUrl is what Swagger uses for the Authorize button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and verifies JWT token from Authorization header.
    Returns the user object if valid.
    Raises 401 if anything is wrong.
    """
    try:
        payload = decode_access_token(token)
        user_id: int = payload.get("user_id")

        if user_id is None:
            raise InvalidTokenError()

    except ExpiredSignatureError:
        # Token existed but has expired
        raise TokenExpiredError()

    except JWTError:
        # Token is malformed or signature is invalid
        raise InvalidTokenError()

    # Confirm user still exists in DB
    user = db.get(User, user_id)
    if not user:
        raise InvalidTokenError()

    # Confirm user account is still active
    if not user.is_active:
        raise InvalidTokenError()

    return user