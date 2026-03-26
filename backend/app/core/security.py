from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import bcrypt

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# ==================== PAROL HASHLASH ====================

class PasswordHasher:
    """
    Parol hashlash uchun klass
    Bcrypt algoritmi bilan ishlaydi, 72 bayt cheklovini avtomatik hal qiladi
    """
    
    @staticmethod
    def hash(password: str) -> str:
        """
        Parolni bcrypt bilan hashlash
        
        Args:
            password: Hashlanadigan parol
            
        Returns:
            str: Hashlangan parol
            
        Raises:
            ValueError: Agar parol bo'sh bo'lsa
        """
        if not password:
            raise ValueError("Parol bo'sh bo'lishi mumkin emas")
        
        # Bcrypt maksimum 72 bayt qabul qiladi
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Bcrypt bilan hashlash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """
        Parolni hash bilan solishtirish
        
        Args:
            plain_password: Oddiy matnli parol
            hashed_password: Hashlangan parol
            
        Returns:
            bool: Parollar mos kelsa True, aks holda False
        """
        if not plain_password or not hashed_password:
            return False
        
        # Parolni 72 baytgacha qisqartirish
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        try:
            return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
        except Exception:
            return False


# ==================== AUTHENTICATION ====================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT Authentication"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Oddiy matnli parolni hash bilan solishtirish
    
    Args:
        plain_password: Oddiy matnli parol
        hashed_password: Hashlangan parol
        
    Returns:
        bool: Parollar mos kelsa True, aks holda False
    """
    return PasswordHasher.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Parolni bcrypt algoritmi bilan hashlash
    
    Args:
        password: Hashlanadigan parol
        
    Returns:
        str: Hashlangan parol
    """
    return PasswordHasher.hash(password)


# ==================== TOKEN FUNKSIYALARI ====================

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Access token yaratish
    
    Args:
        data: Token ichiga qo'shiladigan ma'lumotlar
        expires_delta: Token muddati (agar berilmasa, config'dagi vaqt ishlatiladi)
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    # Token muddatini hisoblash
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Token ma'lumotlarini qo'shish
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })
    
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )


def create_refresh_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Refresh token yaratish
    
    Args:
        data: Token ichiga qo'shiladigan ma'lumotlar
        expires_delta: Token muddati (agar berilmasa, config'dagi vaqt ishlatiladi)
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    # Token muddatini hisoblash
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    # Token ma'lumotlarini qo'shish
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })
    
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )


def decode_token(token: str) -> Optional[dict]:
    """
    Tokenni dekod qilish va tekshirish
    
    Args:
        token: JWT token
        
    Returns:
        Optional[dict]: Token valid bo'lsa payload, aks holda None
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True}
        )
        return payload
    except JWTError:
        return None
    except Exception:
        return None


def verify_token_type(token: str, expected_type: str) -> bool:
    """
    Token turini tekshirish (access yoki refresh)
    
    Args:
        token: JWT token
        expected_type: Kutilayotgan token turi ("access" yoki "refresh")
        
    Returns:
        bool: Token turi mos kelsa True, aks holda False
    """
    payload = decode_token(token)
    if not payload:
        return False
    
    token_type = payload.get("type")
    return token_type == expected_type


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Refresh token yordamida yangi access token yaratish
    
    Args:
        refresh_token: Refresh token
        
    Returns:
        Optional[str]: Yangi access token yoki None
    """
    payload = decode_token(refresh_token)
    if not payload:
        return None
    
    # Token turini tekshirish
    if payload.get("type") != "refresh":
        return None
    
    # Token muddatini tekshirish
    exp = payload.get("exp")
    if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
        return None
    
    # Yangi access token yaratish
    user_data = {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "is_owner": payload.get("is_owner", False),
        "is_superuser": payload.get("is_superuser", False)
    }
    
    return create_access_token(user_data)


def is_token_expired(token: str) -> bool:
    """
    Token muddati o'tganligini tekshirish
    
    Args:
        token: JWT token
        
    Returns:
        bool: Token muddati o'tgan bo'lsa True, aks holda False
    """
    payload = decode_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    return datetime.utcnow() > datetime.fromtimestamp(exp)


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Tokenning muddati tugash vaqtini olish
    
    Args:
        token: JWT token
        
    Returns:
        Optional[datetime]: Token muddati tugash vaqti yoki None
    """
    payload = decode_token(token)
    if not payload:
        return None
    
    exp = payload.get("exp")
    if exp:
        return datetime.fromtimestamp(exp)
    return None


def get_token_remaining_time(token: str) -> Optional[int]:
    """
    Tokenning qolgan muddatini sekundlarda olish
    
    Args:
        token: JWT token
        
    Returns:
        Optional[int]: Qolgan vaqt (sekund) yoki None
    """
    expiration = get_token_expiration(token)
    if not expiration:
        return None
    
    remaining = expiration - datetime.utcnow()
    if remaining.total_seconds() < 0:
        return 0
    
    return int(remaining.total_seconds())


# ==================== CURRENT USER FUNKSIYALARI ====================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Tokendan joriy foydalanuvchini olish
    
    Args:
        token: JWT token
        db: Database sessiyasi
        
    Returns:
        User: Joriy foydalanuvchi
        
    Raises:
        HTTPException: Agar token invalid yoki foydalanuvchi topilmasa
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Tokenni dekod qilish
    payload = decode_token(token)
    if not payload:
        raise credentials_exception
    
    # Foydalanuvchi ID sini olish
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    
    # Foydalanuvchini bazadan olish
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise credentials_exception
    
    # Foydalanuvchi aktivligini tekshirish
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Aktiv foydalanuvchini olish
    
    Args:
        current_user: Joriy foydalanuvchi
        
    Returns:
        User: Aktiv foydalanuvchi
        
    Raises:
        HTTPException: Agar foydalanuvchi aktiv bo'lmasa
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Superuser foydalanuvchini olish
    
    Args:
        current_user: Joriy foydalanuvchi
        
    Returns:
        User: Superuser foydalanuvchi
        
    Raises:
        HTTPException: Agar foydalanuvchi superuser bo'lmasa
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser required."
        )
    return current_user


async def get_current_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Owner foydalanuvchini olish
    
    Args:
        current_user: Joriy foydalanuvchi
        
    Returns:
        User: Owner foydalanuvchi
        
    Raises:
        HTTPException: Agar foydalanuvchi owner bo'lmasa
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Owner required."
        )
    return current_user


# ==================== PERMISSION FUNKSIYALARI ====================

def check_permission(
    user: User,
    required_owner: bool = False,
    required_superuser: bool = False
) -> bool:
    """
    Foydalanuvchi ruxsatlarini tekshirish
    
    Args:
        user: Tekshiriladigan foydalanuvchi
        required_owner: Owner ruxsati kerakmi
        required_superuser: Superuser ruxsati kerakmi
        
    Returns:
        bool: Ruxsatlar mos kelsa True, aks holda False
    """
    if required_superuser:
        return user.is_superuser
    
    if required_owner:
        return user.is_owner or user.is_superuser
    
    return True


def require_permission(
    required_owner: bool = False,
    required_superuser: bool = False
):
    """
    Ruxsat tekshirish uchun dependency
    
    Args:
        required_owner: Owner ruxsati kerakmi
        required_superuser: Superuser ruxsati kerakmi
        
    Returns:
        Callable: Dependency funksiyasi
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not check_permission(current_user, required_owner, required_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    
    return permission_checker


# ==================== PASSWORD VALIDATION ====================

def validate_password_strength(password: str) -> dict:
    """
    Parol kuchliligini tekshirish
    
    Args:
        password: Tekshiriladigan parol
        
    Returns:
        dict: Tekshiruv natijalari
    """
    errors = []
    warnings = []
    strength = "weak"
    score = 0
    
    # Uzunlik tekshiruvi
    if len(password) < 8:
        errors.append("Parol kamida 8 ta belgidan iborat bo'lishi kerak")
    elif len(password) >= 12:
        score += 2
    elif len(password) >= 10:
        score += 1
    
    # Katta harf tekshiruvi
    if any(c.isupper() for c in password):
        score += 1
    else:
        warnings.append("Katta harf qo'shish tavsiya etiladi")
    
    # Kichik harf tekshiruvi
    if any(c.islower() for c in password):
        score += 1
    else:
        warnings.append("Kichik harf qo'shish tavsiya etiladi")
    
    # Raqam tekshiruvi
    if any(c.isdigit() for c in password):
        score += 1
    else:
        warnings.append("Raqam qo'shish tavsiya etiladi")
    
    # Maxsus belgi tekshiruvi
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        score += 1
    else:
        warnings.append("Maxsus belgi qo'shish tavsiya etiladi")
    
    # Kuchlilik darajasini aniqlash
    if score >= 5:
        strength = "strong"
    elif score >= 3:
        strength = "medium"
    else:
        strength = "weak"
        errors.append("Parol juda zaif")
    
    return {
        "strength": strength,
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "is_valid": len(errors) == 0
    }