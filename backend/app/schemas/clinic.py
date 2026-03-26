from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime, time
from enum import Enum


# ==================== CLINIC ENUMS ====================

class ClinicType(str, Enum):
    """Klinika turlari"""
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    DENTAL = "dental"
    LABORATORY = "laboratory"
    DIAGNOSTIC = "diagnostic"
    REHABILITATION = "rehabilitation"
    OTHER = "other"


class ClinicStatus(str, Enum):
    """Klinika holati"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


# ==================== CLINIC BASE SCHEMAS ====================

class ClinicBase(BaseModel):
    """Asosiy clinic schema"""
    name: str = Field(..., min_length=2, max_length=255, description="Clinic name")
    address: str = Field(..., min_length=5, max_length=500, description="Clinic address")
    phone: str = Field(..., max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    description: Optional[str] = Field(None, max_length=1000, description="Clinic description")
    clinic_type: Optional[ClinicType] = Field(ClinicType.CLINIC, description="Clinic type")
    
    class Config:
        use_enum_values = True


class ClinicCreate(ClinicBase):
    """Klinika yaratish uchun schema"""
    owner_id: Optional[int] = Field(None, description="Owner user ID")
    working_hours_start: Optional[str] = Field("09:00", description="Working hours start")
    working_hours_end: Optional[str] = Field("18:00", description="Working hours end")
    break_start: Optional[str] = Field("13:00", description="Break start")
    break_end: Optional[str] = Field("14:00", description="Break end")
    working_days: Optional[List[int]] = Field([1, 2, 3, 4, 5], description="Working days (1=Monday, 7=Sunday)")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Telefon raqamini tekshirish"""
        if v:
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 9:
                raise ValueError('Phone number must be at least 9 digits')
        return v
    
    @validator('working_hours_start', 'working_hours_end', 'break_start', 'break_end')
    def validate_time(cls, v):
        """Vaqt formatini tekshirish"""
        if v:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError('Time must be in HH:MM format')
        return v


class ClinicUpdate(BaseModel):
    """Klinika ma'lumotlarini yangilash uchun schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    clinic_type: Optional[ClinicType] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    working_days: Optional[List[int]] = None
    is_active: Optional[bool] = None
    
    class Config:
        use_enum_values = True


# ==================== CLINIC RESPONSE SCHEMAS ====================

class ClinicResponse(ClinicBase):
    """Klinika javob schemasi"""
    id: int
    owner_id: Optional[int] = None
    is_active: bool = True
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    working_days: Optional[List[int]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ClinicDetailResponse(ClinicResponse):
    """Klinika batafsil ma'lumotlari"""
    doctors_count: int = Field(default=0, description="Number of doctors")
    staff_count: int = Field(default=0, description="Number of staff")
    patients_count: int = Field(default=0, description="Number of patients")
    appointments_count: int = Field(default=0, description="Number of appointments")
    appointments_today: int = Field(default=0, description="Appointments today")
    total_revenue: float = Field(default=0.0, description="Total revenue")
    monthly_revenue: float = Field(default=0.0, description="Monthly revenue")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Clinic rating")
    owner_name: Optional[str] = Field(None, description="Owner full name")
    owner_email: Optional[str] = Field(None, description="Owner email")


class ClinicListResponse(BaseModel):
    """Klinikalar ro'yxati javob schemasi"""
    items: List[ClinicResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== CLINIC STATISTICS ====================

class ClinicStats(BaseModel):
    """Klinika statistikasi"""
    total_clinics: int = Field(default=0, description="Total clinics")
    active_clinics: int = Field(default=0, description="Active clinics")
    inactive_clinics: int = Field(default=0, description="Inactive clinics")
    clinics_by_type: dict = Field(default_factory=dict, description="Clinics by type")
    total_doctors: int = Field(default=0, description="Total doctors")
    total_patients: int = Field(default=0, description="Total patients")
    total_appointments: int = Field(default=0, description="Total appointments")
    total_revenue: float = Field(default=0.0, description="Total revenue")
    average_rating: float = Field(default=0.0, description="Average rating")


class ClinicMonthlyStats(BaseModel):
    """Klinika oylik statistikasi"""
    month: str
    year: int
    appointments_count: int
    new_patients: int
    revenue: float
    expenses: Optional[float] = None
    profit: Optional[float] = None


# ==================== CLINIC WORKING HOURS ====================

class WorkingHours(BaseModel):
    """Ish vaqtlari"""
    day: int = Field(..., ge=1, le=7, description="Day of week (1=Monday, 7=Sunday)")
    start: str = Field(..., description="Start time (HH:MM)")
    end: str = Field(..., description="End time (HH:MM)")
    is_working: bool = Field(True, description="Is working day")
    
    @validator('start', 'end')
    def validate_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError('Time must be in HH:MM format')
        return v


class ClinicSchedule(BaseModel):
    """Klinika ish jadvali"""
    clinic_id: int
    clinic_name: str
    working_hours: List[WorkingHours]
    special_days: Optional[List[dict]] = Field(default_factory=list, description="Special working days")
    holidays: Optional[List[dict]] = Field(default_factory=list, description="Holidays")


# ==================== CLINIC FILTERS ====================

class ClinicFilter(BaseModel):
    """Klinika filtrlari"""
    name: Optional[str] = Field(None, description="Search by name")
    city: Optional[str] = Field(None, description="Filter by city")
    clinic_type: Optional[ClinicType] = None
    is_active: Optional[bool] = None
    has_emergency: Optional[bool] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    
    class Config:
        use_enum_values = True


# ==================== CLINIC DOCTORS ====================

class ClinicDoctor(BaseModel):
    """Klinika shifokori"""
    id: int
    full_name: str
    specialization: str
    room_number: Optional[str] = None
    experience_years: int = 0
    rating: float = 0.0
    consultation_fee: float = 0.0
    is_available: bool = True


class ClinicDoctorsResponse(BaseModel):
    """Klinika shifokorlari javobi"""
    clinic_id: int
    clinic_name: str
    doctors: List[ClinicDoctor]
    total_doctors: int


# ==================== CLINIC SERVICES ====================

class ClinicService(BaseModel):
    """Klinika xizmati"""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    duration: int = Field(..., description="Duration in minutes")
    category: Optional[str] = None
    is_active: bool = True


class ClinicServicesResponse(BaseModel):
    """Klinika xizmatlari javobi"""
    clinic_id: int
    clinic_name: str
    services: List[ClinicService]
    total_services: int


# ==================== CLINIC REVIEW ====================

class ClinicReview(BaseModel):
    """Klinika sharhi"""
    id: int
    patient_id: int
    patient_name: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime


class ClinicReviewsResponse(BaseModel):
    """Klinika sharhlari javobi"""
    clinic_id: int
    clinic_name: str
    average_rating: float
    total_reviews: int
    reviews: List[ClinicReview]


# ==================== VALIDATION FUNCTIONS ====================

def validate_working_hours(start: str, end: str) -> bool:
    """
    Ish vaqtlarini tekshirish
    
    Args:
        start: Boshlanish vaqti
        end: Tugash vaqti
        
    Returns:
        bool: Vaqtlar to'g'ri bo'lsa True
    """
    try:
        start_time = datetime.strptime(start, "%H:%M").time()
        end_time = datetime.strptime(end, "%H:%M").time()
        return start_time < end_time
    except ValueError:
        return False


def get_clinic_working_days(working_days: List[int]) -> List[str]:
    """
    Ish kunlarini nomlarini olish
    
    Args:
        working_days: Ish kunlari raqamlari
        
    Returns:
        List[str]: Ish kunlari nomlari
    """
    days_map = {
        1: "Monday", 2: "Tuesday", 3: "Wednesday",
        4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"
    }
    return [days_map[day] for day in working_days if day in days_map]

# ... (oldingi schemalardan keyin qo'shing)

class ClinicSubscriptionUpdate(BaseModel):
    """Klinika obuna ma'lumotlarini yangilash"""
    subscription_plan: Optional[str] = Field(None, max_length=100)
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    subscription_status: Optional[str] = Field(None, max_length=50)
    auto_renew: Optional[bool] = None
    payment_method_id: Optional[str] = None