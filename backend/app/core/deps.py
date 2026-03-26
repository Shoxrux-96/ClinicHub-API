from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati tugagan"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi"
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Foydalanuvchi faol emas")
    return current_user

# Rol tekshiruvchi dependency factory
def require_roles(*roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amalni bajarish uchun ruxsat yo'q"
            )
        return current_user
    return role_checker

# Tayyor dependency lar
def require_owner(user: User = Depends(require_roles(UserRole.OWNER))) -> User:
    return user

def require_admin(user: User = Depends(
    require_roles(UserRole.OWNER, UserRole.ADMIN)
)) -> User:
    return user

def require_doctor(user: User = Depends(
    require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.DOCTOR)
)) -> User:
    return user

def require_reception(user: User = Depends(
    require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTION)
)) -> User:
    return user

# Clinic ID tekshiruvi — owner barcha klinikani ko'radi, boshqalar faqat o'zinikini
def check_clinic_access(clinic_id: int, current_user: User) -> bool:
    if current_user.role == UserRole.OWNER:
        return True
    if current_user.clinic_id != clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu klinikaga kirish ruxsati yo'q"
        )
    return True