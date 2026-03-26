from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from typing import List, Optional
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserChangePassword
from app.core.security import get_password_hash, verify_password

class UserService:

    @staticmethod
    def get_all(db: Session, clinic_id: int, role: Optional[UserRole] = None) -> List[User]:
        query = db.query(User).filter(
            User.clinic_id == clinic_id,
            User.is_deleted == False
        )
        if role:
            query = query.filter(User.role == role)
        return query.all()

    @staticmethod
    def get_by_id(db: Session, user_id: int, clinic_id: Optional[int] = None) -> User:
        query = db.query(User).filter(User.id == user_id, User.is_deleted == False)
        if clinic_id:
            query = query.filter(User.clinic_id == clinic_id)
        user = query.first()
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        return user

    @staticmethod
    def create(db: Session, clinic_id: int, data: UserCreate) -> User:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bu email allaqachon ro'yxatdan o'tgan")

        # Owner faqat admin yaratishi mumkin, admin esa doctor/reception
        user = User(
            clinic_id=clinic_id,
            role=data.role,
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            password_hash=get_password_hash(data.password),
            specialization=data.specialization,
            room_number=data.room_number,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user_id: int, clinic_id: int, data: UserUpdate) -> User:
        user = UserService.get_by_id(db, user_id, clinic_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user_id: int, data: UserChangePassword) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Eski parol noto'g'ri")
        user.password_hash = get_password_hash(data.new_password)
        db.commit()
        return {"message": "Parol muvaffaqiyatli o'zgartirildi"}

    @staticmethod
    def delete(db: Session, user_id: int, clinic_id: int):
        user = UserService.get_by_id(db, user_id, clinic_id)
        user.is_deleted = True
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        db.commit()