from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserBriefInfo"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserBriefInfo(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    clinic_id: Optional[int] = None

    class Config:
        from_attributes = True

TokenResponse.model_rebuild()