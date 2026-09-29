from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_token_payload
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user, account = AuthService(db).register(data)
    return RegisterResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        account_number=account.account_number,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token = AuthService(db).login(data)
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: dict = Depends(get_token_payload),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(db).logout(payload)
    return MessageResponse(message="Logged out successfully")
