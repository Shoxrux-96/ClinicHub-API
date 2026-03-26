from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from app.models.user import User, UserRole
from app.models.clinic import Clinic
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginRequest, TokenResponse, UserBriefInfo
from app.core.config import settings

class AuthService:

    @staticmethod
    def login(db: Session, data: LoginRequest) -> TokenResponse:
        user = db.query(User).filter(
            User.email == data.email,
            User.is_deleted == False
        ).first()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email yoki parol noto'g'ri"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hisobingiz faol emas. Admin bilan bog'laning"
            )

        # Klinika obunasini tekshirish (owner uchun emas)
        if user.role != UserRole.OWNER and user.clinic_id:
            clinic = db.query(Clinic).filter(Clinic.id == user.clinic_id).first()
            if not clinic or not clinic.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Klinika faol emas"
                )
            if clinic.subscription_end and clinic.subscription_end < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Klinika obunasi tugagan. Admin bilan bog'laning"
                )

        # Last login yangilash
        user.last_login = datetime.utcnow()
        db.commit()

        token_data = {"sub": str(user.id), "role": user.role, "clinic_id": user.clinic_id}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserBriefInfo.model_validate(user)
        )

    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token yaroqsiz"
            )

        user = db.query(User).filter(
            User.id == int(payload["sub"]),
            User.is_active == True,
            User.is_deleted == False
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Foydalanuvchi topilmadi"
            )

        token_data = {"sub": str(user.id), "role": user.role, "clinic_id": user.clinic_id}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=UserBriefInfo.model_validate(user)
        )

    @staticmethod
    def create_first_owner(db: Session):
        existing = db.query(User).filter(User.role == UserRole.OWNER).first()
        if existing:
            return

        owner = User(
            role=UserRole.OWNER,
            full_name=settings.FIRST_OWNER_NAME,
            email=settings.FIRST_OWNER_EMAIL,
            password_hash=get_password_hash(settings.FIRST_OWNER_PASSWORD),
            is_active=True
        )
        db.add(owner)
        db.commit()
        print(f"✅ First owner yaratildi: {settings.FIRST_OWNER_EMAIL}")