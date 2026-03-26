from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, time
from enum import Enum
import re


# ==================== SERVICE ENUMS ====================

class ServiceCategory(str, Enum):
    """Xizmat kategoriyalari"""
    CONSULTATION = "consultation"
    DIAGNOSTIC = "diagnostic"
    LABORATORY = "laboratory"
    RADIOLOGY = "radiology"
    SURGERY = "surgery"
    DENTAL = "dental"
    VACCINATION = "vaccination"
    PHYSIOTHERAPY = "physiotherapy"
    WELLNESS = "wellness"
    EMERGENCY = "emergency"
    OTHER = "other"


class ServiceStatus(str, Enum):
    """Xizmat holati"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class ServicePricingType(str, Enum):
    """Narxlash turi"""
    FIXED = "fixed"
    HOURLY = "hourly"
    PER_SESSION = "per_session"
    PER_UNIT = "per_unit"
    PACKAGE = "package"


# ==================== SERVICE BASE SCHEMAS ====================

class ServiceBase(BaseModel):
    """Asosiy service schema"""
    name: str = Field(..., min_length=2, max_length=255, description="Service name")
    description: Optional[str] = Field(None, max_length=1000, description="Service description")
    category: ServiceCategory = Field(ServiceCategory.CONSULTATION, description="Service category")
    price: float = Field(..., ge=0, description="Service price")
    duration: int = Field(30, ge=5, le=480, description="Duration in minutes")
    clinic_id: int = Field(..., description="Clinic ID")
    is_active: bool = Field(True, description="Is service active")
    
    class Config:
        use_enum_values = True


class ServiceCreate(ServiceBase):
    """Xizmat yaratish uchun schema"""
    discount_percentage: Optional[float] = Field(0, ge=0, le=100)
    discount_start_date: Optional[datetime] = None
    discount_end_date: Optional[datetime] = None
    requires_doctor: bool = Field(True)
    requires_referral: bool = Field(False)
    insurance_accepted: bool = Field(True)
    preparation_instructions: Optional[str] = Field(None, max_length=2000)
    aftercare_instructions: Optional[str] = Field(None, max_length=2000)


class ServiceUpdate(BaseModel):
    """Xizmat ma'lumotlarini yangilash uchun schema"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[ServiceCategory] = None
    price: Optional[float] = Field(None, ge=0)
    duration: Optional[int] = Field(None, ge=5, le=480)
    is_active: Optional[bool] = None
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_start_date: Optional[datetime] = None
    discount_end_date: Optional[datetime] = None
    requires_doctor: Optional[bool] = None
    requires_referral: Optional[bool] = None
    insurance_accepted: Optional[bool] = None
    preparation_instructions: Optional[str] = Field(None, max_length=2000)
    aftercare_instructions: Optional[str] = Field(None, max_length=2000)
    
    class Config:
        use_enum_values = True


# ==================== SERVICE RESPONSE SCHEMAS ====================

class ServiceResponse(ServiceBase):
    """Xizmat javob schemasi"""
    id: int
    discount_percentage: float = 0
    discount_start_date: Optional[datetime] = None
    discount_end_date: Optional[datetime] = None
    requires_doctor: bool = True
    requires_referral: bool = False
    insurance_accepted: bool = True
    preparation_instructions: Optional[str] = None
    aftercare_instructions: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_bookings: int = 0
    average_rating: float = 0
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ServiceDetailResponse(ServiceResponse):
    """Xizmat batafsil ma'lumotlari"""
    clinic_name: str
    clinic_address: Optional[str] = None
    doctors: List[dict] = Field(default_factory=list)
    reviews: List[dict] = Field(default_factory=list)
    available_times: List[str] = Field(default_factory=list)


class ServiceListResponse(BaseModel):
    """Xizmatlar ro'yxati javob schemasi"""
    items: List[ServiceResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== SERVICE PRICING ====================

class ServicePricing(BaseModel):
    """Xizmat narxlari"""
    service_id: int
    service_name: str
    base_price: float
    current_price: float
    discount_percentage: float = 0
    discount_amount: float = 0
    discount_valid_until: Optional[datetime] = None
    price_valid_from: Optional[datetime] = None
    price_valid_to: Optional[datetime] = None
    pricing_type: ServicePricingType = ServicePricingType.FIXED
    
    class Config:
        use_enum_values = True


# ==================== SERVICE FILTERS ====================

class ServiceFilter(BaseModel):
    """Xizmat filtrlari"""
    name: Optional[str] = Field(None, description="Search by name")
    category: Optional[ServiceCategory] = None
    clinic_id: Optional[int] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_duration: Optional[int] = Field(None, ge=5)
    max_duration: Optional[int] = Field(None, le=480)
    is_active: Optional[bool] = None
    has_discount: Optional[bool] = None
    requires_doctor: Optional[bool] = None
    insurance_accepted: Optional[bool] = None
    
    class Config:
        use_enum_values = True


# ==================== SERVICE STATISTICS ====================

class ServiceStats(BaseModel):
    """Xizmatlar statistikasi"""
    total_services: int
    active_services: int
    inactive_services: int
    services_by_category: dict = Field(default_factory=dict)
    total_revenue: float
    average_price: float
    most_booked_services: List[dict] = Field(default_factory=list)
    highest_rated_services: List[dict] = Field(default_factory=list)
    services_with_discount: int


class ServiceBookingStats(BaseModel):
    """Xizmat bandlik statistikasi"""
    service_id: int
    service_name: str
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: float
    average_rating: float
    monthly_bookings: List[dict] = Field(default_factory=list)


# ==================== SERVICE DURATION ====================

class ServiceDuration(BaseModel):
    """Xizmat davomiyligi"""
    duration: int
    unit: str = "minutes"
    buffer_before: int = 0
    buffer_after: int = 0
    total_duration: int


# ==================== SERVICE AVAILABILITY ====================

class ServiceAvailability(BaseModel):
    """Xizmat mavjudligi"""
    service_id: int
    service_name: str
    is_available: bool
    available_slots: int
    next_available: Optional[datetime] = None
    waiting_time: Optional[int] = None


# ==================== SERVICE REVIEW ====================

class ServiceReview(BaseModel):
    """Xizmat sharhi"""
    id: int
    service_id: int
    patient_id: int
    patient_name: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime


class ServiceReviewCreate(BaseModel):
    """Xizmat sharhi yaratish"""
    service_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


# ==================== SERVICE PACKAGE ====================

class ServicePackage(BaseModel):
    """Xizmatlar paketi"""
    id: int
    name: str
    description: Optional[str] = None
    services: List[int]
    total_price: float
    discount_percentage: float
    final_price: float
    valid_days: int = 365
    is_active: bool = True


class ServicePackageCreate(BaseModel):
    """Xizmatlar paketi yaratish"""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    service_ids: List[int]
    discount_percentage: float = Field(..., ge=0, le=100)
    valid_days: int = Field(365, ge=1, le=730)
    is_active: bool = True


# ==================== SERVICE PROMOTION ====================

class ServicePromotion(BaseModel):
    """Xizmat aksiyasi"""
    id: int
    service_id: int
    title: str
    description: Optional[str] = None
    discount_percentage: float
    start_date: datetime
    end_date: datetime
    is_active: bool = True


# ==================== VALIDATION FUNCTIONS ====================

def validate_service_name(name: str) -> bool:
    """
    Xizmat nomini tekshirish
    
    Args:
        name: Xizmat nomi
        
    Returns:
        bool: Valid bo'lsa True
    """
    if len(name) < 2:
        return False
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        return False
    return True


def calculate_discounted_price(price: float, discount_percentage: float) -> float:
    """
    Chegirmali narxni hisoblash
    
    Args:
        price: Asosiy narx
        discount_percentage: Chegirma foizi
        
    Returns:
        float: Chegirmali narx
    """
    return price * (1 - discount_percentage / 100)


def is_discount_valid(
    discount_start_date: Optional[datetime],
    discount_end_date: Optional[datetime]
) -> bool:
    """
    Chegirma amal qilish muddatini tekshirish
    
    Returns:
        bool: Chegirma amal qilsa True
    """
    now = datetime.now()
    
    if discount_start_date and discount_start_date > now:
        return False
    
    if discount_end_date and discount_end_date < now:
        return False
    
    return True


def get_service_price_with_discount(service: dict) -> float:
    """
    Chegirma bilan xizmat narxini olish
    
    Args:
        service: Xizmat ma'lumotlari
        
    Returns:
        float: Chegirmali narx
    """
    price = service.get('price', 0)
    discount = service.get('discount_percentage', 0)
    
    if discount > 0 and is_discount_valid(
        service.get('discount_start_date'),
        service.get('discount_end_date')
    ):
        return calculate_discounted_price(price, discount)
    
    return price


def calculate_total_duration(services: List[dict]) -> int:
    """
    Xizmatlar umumiy davomiyligini hisoblash
    
    Args:
        services: Xizmatlar ro'yxati
        
    Returns:
        int: Umumiy davomiylik (daqiqa)
    """
    total = 0
    for service in services:
        total += service.get('duration', 0)
    return total