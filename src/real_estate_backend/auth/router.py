from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from real_estate_backend.core.database import get_db
from real_estate_backend.auth.schema import SignupRequest, LoginRequest, TokenResponse, UserResponse
from real_estate_backend.auth import service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    return service.signup(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return service.login(db, data)


@router.post("/logout")
def logout():
    # JWT is stateless — server cannot invalidate token
    # Client is responsible for discarding it
    return {"message": "Logged out successfully. Please discard your token."}