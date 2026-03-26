from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
import re


# ==================== PAYMENT ENUMS ====================

class PaymentMethod(str, Enum):
    """To'lov usullari"""
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_PAYMENT = "mobile_payment"
    ONLINE = "online"
    INSURANCE = "insurance"
    OTHER = "other"


class PaymentStatus(str, Enum):
    """To'lov holati"""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    PROCESSING = "processing"


class PaymentType(str, Enum):
    """To'lov turi"""
    CONSULTATION = "consultation"
    SERVICE = "service"
    PROCEDURE = "procedure"
    MEDICATION = "medication"
    PACKAGE = "package"
    DEPOSIT = "deposit"
    OTHER = "other"


# ==================== PAYMENT BASE SCHEMAS ====================

class PaymentBase(BaseModel):
    """Asosiy payment schema"""
    appointment_id: Optional[int] = Field(None, description="Appointment ID")
    patient_id: int = Field(..., description="Patient ID")
    clinic_id: int = Field(..., description="Clinic ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    method: PaymentMethod = Field(..., description="Payment method")
    type: PaymentType = Field(PaymentType.CONSULTATION, description="Payment type")
    status: PaymentStatus = Field(PaymentStatus.PENDING, description="Payment status")
    description: Optional[str] = Field(None, max_length=500, description="Payment description")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    class Config:
        use_enum_values = True


class PaymentCreate(PaymentBase):
    """To'lov yaratish uchun schema"""
    transaction_id: Optional[str] = Field(None, max_length=255, description="Transaction ID")
    payment_date: Optional[datetime] = Field(default_factory=datetime.now)
    receipt_number: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class PaymentUpdate(BaseModel):
    """To'lov ma'lumotlarini yangilash uchun schema"""
    amount: Optional[float] = Field(None, gt=0)
    method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    description: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    transaction_id: Optional[str] = Field(None, max_length=255)
    refund_amount: Optional[float] = Field(None, ge=0)
    refund_reason: Optional[str] = Field(None, max_length=500)
    refund_date: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


# ==================== PAYMENT RESPONSE SCHEMAS ====================

class PaymentResponse(PaymentBase):
    """To'lov javob schemasi"""
    id: int
    transaction_id: Optional[str] = None
    receipt_number: Optional[str] = None
    payment_date: datetime
    refund_amount: float = 0
    refund_reason: Optional[str] = None
    refund_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class PaymentDetailResponse(PaymentResponse):
    """To'lov batafsil ma'lumotlari"""
    patient_name: str
    patient_phone: Optional[str] = None
    clinic_name: str
    appointment_date: Optional[datetime] = None
    service_names: List[str] = Field(default_factory=list)
    remaining_balance: float = 0


class PaymentListResponse(BaseModel):
    """To'lovlar ro'yxati javob schemasi"""
    items: List[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== PAYMENT STATISTICS ====================

class PaymentStatistics(BaseModel):
    """To'lov statistikasi"""
    total_payments: int
    total_amount: float
    total_paid: float
    total_pending: float
    total_refunded: float
    average_payment: float
    payments_by_method: dict = Field(default_factory=dict)
    payments_by_status: dict = Field(default_factory=dict)
    daily_revenue: List[dict] = Field(default_factory=list)
    weekly_revenue: List[dict] = Field(default_factory=list)
    monthly_revenue: List[dict] = Field(default_factory=list)
    yearly_revenue: List[dict] = Field(default_factory=list)


class RevenueStats(BaseModel):
    """Daromad statistikasi"""
    today: float
    this_week: float
    this_month: float
    this_year: float
    last_month: float
    last_year: float
    growth_percentage: float
    projected_revenue: float


# ==================== PAYMENT FILTERS ====================

class PaymentFilter(BaseModel):
    """To'lov filtrlari"""
    patient_id: Optional[int] = None
    clinic_id: Optional[int] = None
    appointment_id: Optional[int] = None
    method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None
    type: Optional[PaymentType] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = Field(None, description="Search by patient name or receipt number")
    
    class Config:
        use_enum_values = True


# ==================== PAYMENT RECEIPT ====================

class PaymentReceipt(BaseModel):
    """To'lov kvitansiyasi"""
    receipt_number: str
    payment_id: int
    clinic_name: str
    clinic_address: str
    clinic_phone: str
    patient_name: str
    patient_phone: str
    patient_address: Optional[str] = None
    payment_date: datetime
    amount: float
    method: PaymentMethod
    description: Optional[str] = None
    services: List[dict] = Field(default_factory=list)
    subtotal: float
    tax: float = 0
    discount: float = 0
    total: float
    amount_in_words: str
    
    class Config:
        use_enum_values = True


# ==================== REFUND ====================

class RefundRequest(BaseModel):
    """To'lovni qaytarish so'rovi"""
    payment_id: int
    amount: float = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=500)
    
    @validator('amount')
    def validate_amount(cls, v, values):
        if 'payment_id' in values:
            # Bu yerda to'lov miqdorini tekshirish kerak
            pass
        return v


class RefundResponse(BaseModel):
    """To'lovni qaytarish javobi"""
    refund_id: int
    payment_id: int
    amount: float
    reason: str
    status: str
    refund_date: datetime
    transaction_id: Optional[str] = None


# ==================== INVOICE ====================

class Invoice(BaseModel):
    """Hisob-faktura"""
    invoice_number: str
    payment_id: int
    clinic_name: str
    clinic_tax_id: Optional[str] = None
    patient_name: str
    patient_tax_id: Optional[str] = None
    issue_date: date
    due_date: date
    items: List[dict]
    subtotal: float
    tax_rate: float = 0
    tax_amount: float = 0
    discount: float = 0
    total: float
    paid_amount: float = 0
    balance_due: float
    status: str = "pending"


# ==================== PAYMENT SUMMARY ====================

class PaymentSummary(BaseModel):
    """To'lov xulosasi"""
    patient_id: int
    patient_name: str
    total_balance: float
    pending_payments: List[PaymentResponse]
    payment_history: List[PaymentResponse]


class ClinicPaymentSummary(BaseModel):
    """Klinika to'lov xulosasi"""
    clinic_id: int
    clinic_name: str
    total_revenue: float
    today_revenue: float
    this_week_revenue: float
    this_month_revenue: float
    pending_payments: int
    pending_amount: float
    completed_payments: int
    completed_amount: float
    refunded_amount: float


# ==================== PAYMENT REPORT ====================

class PaymentReport(BaseModel):
    """To'lov hisoboti"""
    period: str
    start_date: datetime
    end_date: datetime
    total_transactions: int
    total_amount: float
    average_transaction: float
    highest_transaction: float
    lowest_transaction: float
    payments_by_method: dict
    payments_by_day: List[dict]
    export_url: Optional[str] = None


# ==================== VALIDATION FUNCTIONS ====================

def generate_receipt_number(clinic_id: int, payment_id: int) -> str:
    """
    Kvitansiya raqamini yaratish
    
    Args:
        clinic_id: Klinika ID
        payment_id: To'lov ID
        
    Returns:
        str: Kvitansiya raqami
    """
    date_str = datetime.now().strftime("%Y%m%d")
    return f"RCP-{clinic_id:04d}-{date_str}-{payment_id:06d}"


def generate_invoice_number(clinic_id: int, payment_id: int) -> str:
    """
    Hisob-faktura raqamini yaratish
    
    Args:
        clinic_id: Klinika ID
        payment_id: To'lov ID
        
    Returns:
        str: Hisob-faktura raqami
    """
    date_str = datetime.now().strftime("%Y%m")
    return f"INV-{clinic_id:04d}-{date_str}-{payment_id:06d}"


def amount_to_words(amount: float, currency: str = "UZS") -> str:
    """
    Pul miqdorini so'z bilan yozish
    
    Args:
        amount: Pul miqdori
        currency: Valyuta
        
    Returns:
        str: So'z bilan yozilgan miqdor
    """
    # Oddiy versiya, kerak bo'lsa to'liq yozish mumkin
    return f"{amount:,.2f} {currency}"


def calculate_tax(amount: float, tax_rate: float = 0) -> float:
    """
    Soliqni hisoblash
    
    Args:
        amount: Asosiy summa
        tax_rate: Soliq stavkasi (foizda)
        
    Returns:
        float: Soliq summasi
    """
    return amount * (tax_rate / 100)


def calculate_total_with_tax(amount: float, tax_rate: float = 0) -> float:
    """
    Soliq bilan umumiy summani hisoblash
    
    Args:
        amount: Asosiy summa
        tax_rate: Soliq stavkasi (foizda)
        
    Returns:
        float: Soliq bilan umumiy summa
    """
    return amount + calculate_tax(amount, tax_rate)