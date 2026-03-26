from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ==================== USER ROLE ====================

class UserRole(str, Enum):
    """Foydalanuvchi rollari"""
    OWNER = "owner"
    SUPERUSER = "superuser"
    ADMIN = "admin"
    DOCTOR = "doctor"
    STAFF = "staff"
    USER = "user"


# ==================== USER BASE SCHEMA ====================

class UserBase(BaseModel):
    """Asosiy user schema"""
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    role: UserRole = Field(UserRole.USER, description="User role")
    specialization: Optional[str] = Field(None, max_length=255, description="Specialization (for doctors)")
    room_number: Optional[str] = Field(None, max_length=50, description="Room number (for doctors)")
    
    class Config:
        use_enum_values = True


# ==================== USER CREATE SCHEMA ====================

class UserCreate(BaseModel):
    """Foydalanuvchi yaratish uchun schema"""
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER
    specialization: Optional[str] = Field(None, max_length=255)
    room_number: Optional[str] = Field(None, max_length=50)
    
    @validator('password')
    def validate_password(cls, v):
        """Parol kuchliligini tekshirish"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Telefon raqamini tekshirish"""
        if v:
            # Faqat raqamlar, + va - belgilarini qoldirish
            digits = ''.join(filter(lambda x: x.isdigit() or x == '+', v))
            if len(digits) < 9:
                raise ValueError('Phone number must be at least 9 digits')
        return v
    
    class Config:
        use_enum_values = True


# ==================== USER UPDATE SCHEMA ====================

class UserUpdate(BaseModel):
    """Foydalanuvchi ma'lumotlarini yangilash uchun schema"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    specialization: Optional[str] = Field(None, max_length=255)
    room_number: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        """Telefon raqamini tekshirish"""
        if v:
            digits = ''.join(filter(lambda x: x.isdigit() or x == '+', v))
            if len(digits) < 9:
                raise ValueError('Phone number must be at least 9 digits')
        return v
    
    class Config:
        use_enum_values = True


# ==================== USER CHANGE PASSWORD SCHEMA ====================

class UserChangePassword(BaseModel):
    """Parol o'zgartirish uchun schema"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Yangi parol kuchliligini tekshirish"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# ==================== USER RESPONSE SCHEMA ====================

class UserResponse(BaseModel):
    """Foydalanuvchi javob schemasi"""
    id: int
    clinic_id: Optional[int] = None
    role: UserRole
    full_name: str
    email: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    room_number: Optional[str] = None
    is_active: bool
    is_owner: bool = False
    is_superuser: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


# ==================== USER DETAIL RESPONSE SCHEMA ====================

class UserDetailResponse(UserResponse):
    """Foydalanuvchi batafsil ma'lumotlari"""
    appointments_count: int = Field(default=0, description="Number of appointments")
    patients_count: int = Field(default=0, description="Number of patients (for doctors)")
    created_by: Optional[str] = None
    permissions: List[str] = Field(default_factory=list, description="User permissions")


# ==================== USER LIST RESPONSE SCHEMA ====================

class UserListResponse(BaseModel):
    """Foydalanuvchilar ro'yxati javob schemasi"""
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== USER FILTER SCHEMA ====================

class UserFilter(BaseModel):
    """Foydalanuvchi filtrlari"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    clinic_id: Optional[int] = None
    search: Optional[str] = Field(None, description="Search by name or email")
    
    class Config:
        use_enum_values = True


# ==================== AUTH SCHEMAS ====================

class Token(BaseModel):
    """Token javob schemasi"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenRefresh(BaseModel):
    """Refresh token schemasi"""
    refresh_token: str


class TokenPayload(BaseModel):
    """Token ichidagi ma'lumotlar"""
    sub: str
    exp: int
    type: str
    iat: Optional[int] = None
    email: Optional[str] = None
    is_owner: Optional[bool] = False
    is_superuser: Optional[bool] = False


class LoginRequest(BaseModel):
    """Login so'rovi schemasi"""
    email: EmailStr
    password: str


class LoginResponse(Token):
    """Login javob schemasi"""
    user: UserResponse


class PasswordReset(BaseModel):
    """Parol tiklash so'rovi schemasi"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Parol tiklashni tasdiqlash schemasi"""
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


# ==================== STAFF SCHEMAS ====================

class StaffCreate(UserCreate):
    """Xodim yaratish schemasi"""
    clinic_id: int
    position: Optional[str] = Field(None, max_length=100)
    hire_date: Optional[datetime] = None


class StaffResponse(UserResponse):
    """Xodim javob schemasi"""
    position: Optional[str] = None
    hire_date: Optional[datetime] = None
    clinic_name: Optional[str] = None


# ==================== DOCTOR SCHEMAS ====================

class DoctorCreate(UserCreate):
    """Shifokor yaratish schemasi"""
    clinic_id: int
    specialization: str = Field(..., max_length=255)
    room_number: str = Field(..., max_length=50)
    experience_years: Optional[int] = Field(0, ge=0, le=50)
    consultation_fee: Optional[float] = Field(0.0, ge=0)
    working_hours: Optional[str] = None
    break_hours: Optional[str] = None


class DoctorResponse(UserResponse):
    """Shifokor javob schemasi"""
    experience_years: int = 0
    consultation_fee: float = 0.0
    working_hours: Optional[str] = None
    break_hours: Optional[str] = None
    clinic_name: Optional[str] = None
    rating: Optional[float] = Field(0.0, ge=0, le=5)
    appointment_count: int = 0


class DoctorSchedule(BaseModel):
    """Shifokor ish jadvali"""
    doctor_id: int
    doctor_name: str
    date: datetime
    start_time: str
    end_time: str
    is_available: bool
    appointments: List[dict] = Field(default_factory=list)


# ==================== USER STATISTICS ====================

class UserStatistics(BaseModel):
    """Foydalanuvchilar statistikasi"""
    total_users: int
    total_doctors: int
    total_staff: int
    total_admins: int
    active_users: int
    inactive_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int


# ==================== VALIDATION FUNCTIONS ====================

def normalize_phone(phone: str) -> str:
    """
    Telefon raqamini normallashtirish
    
    Args:
        phone: Telefon raqami
        
    Returns:
        str: Normallashtirilgan telefon raqami
    """
    if not phone:
        return phone
    
    # Faqat raqamlarni qoldirish
    digits = ''.join(filter(str.isdigit, phone))
    
    # O'zbekiston telefon raqamlari uchun
    if len(digits) == 9:
        return f"+998{digits}"
    elif len(digits) == 12 and digits.startswith("998"):
        return f"+{digits}"
    elif len(digits) == 13 and digits.startswith("998"):
        return f"+{digits}"
    else:
        return phone


def validate_user_role(role: UserRole, allowed_roles: List[UserRole]) -> bool:
    """
    Foydalanuvchi rolini tekshirish
    
    Args:
        role: Foydalanuvchi roli
        allowed_roles: Ruxsat etilgan rollar
        
    Returns:
        bool: Ruxsat etilgan bo'lsa True
    """
    return role in allowed_roles


def get_role_permissions(role: UserRole) -> List[str]:
    """
    Rolga mos ruxsatlarni olish
    
    Args:
        role: Foydalanuvchi roli
        
    Returns:
        List[str]: Ruxsatlar ro'yxati
    """
    permissions = {
        UserRole.OWNER: [
            "create_clinic", "update_clinic", "delete_clinic",
            "manage_users", "manage_doctors", "manage_staff",
            "view_reports", "manage_payments", "all_access"
        ],
        UserRole.SUPERUSER: [
            "manage_users", "manage_doctors", "manage_staff",
            "view_reports", "manage_payments", "all_access"
        ],
        UserRole.ADMIN: [
            "manage_doctors", "manage_staff", "view_reports",
            "manage_appointments", "manage_patients"
        ],
        UserRole.DOCTOR: [
            "view_appointments", "manage_appointments",
            "view_patients", "update_medical_records"
        ],
        UserRole.STAFF: [
            "view_appointments", "create_appointments",
            "view_patients", "manage_payments"
        ],
        UserRole.USER: [
            "view_profile", "update_profile",
            "view_appointments", "create_appointments"
        ]
    }
    
    return permissions.get(role, [])