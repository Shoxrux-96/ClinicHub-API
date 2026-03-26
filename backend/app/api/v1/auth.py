from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserBriefInfo
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return AuthService.login(db, data)

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    return AuthService.refresh_token(db, data.refresh_token)

@router.get("/me", response_model=UserBriefInfo)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    # Client token ni o'chiradi, server tomonda blacklist kerak emas (stateless JWT)
    return {"message": "Muvaffaqiyatli chiqildi"}