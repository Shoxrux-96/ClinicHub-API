from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, JSON, Text, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime


class PaymentMethod(str, enum.Enum):
    """To'lov usullari"""
    CASH = "cash"           # naqd
    CARD = "card"           # karta
    POS = "pos"             # pos terminal
    BANK_TRANSFER = "bank_transfer"  # bank o'tkazmasi
    MOBILE = "mobile"       # mobil to'lov (Payme, Click, etc.)
    INSURANCE = "insurance" # sug'urta
    ONLINE = "online"       # online to'lov


class PaymentStatus(str, enum.Enum):
    """To'lov holati"""
    PAID = "paid"           # to'langan
    PARTIAL = "partial"     # qisman to'langan
    DEBT = "debt"           # qarzdorlik
    PENDING = "pending"     # kutilmoqda
    REFUNDED = "refunded"   # qaytarilgan
    CANCELLED = "cancelled" # bekor qilingan


class PaymentType(str, enum.Enum):
    """To'lov turi"""
    SERVICE = "service"           # xizmat
    SUBSCRIPTION = "subscription" # obuna
    DEPOSIT = "deposit"           # depozit
    PENALTY = "penalty"           # jarima
    OTHER = "other"               # boshqa


class Payment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "payments"
    
    # Indekslar
    __table_args__ = (
        Index('idx_payment_clinic_date', 'clinic_id', 'created_at'),
        Index('idx_payment_patient_status', 'patient_id', 'payment_status'),
        Index('idx_payment_receipt', 'receipt_number'),
        Index('idx_payment_date', 'payment_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    cashier_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Xizmatlar ro'yxati JSON formatda
    # [{"service_id": 1, "service_name": "Konsultatsiya", "price": 50000, "qty": 1, "discount": 0}]
    services_snapshot = Column(JSON, nullable=False)
    
    # To'lov summalari
    subtotal = Column(Numeric(12, 2), nullable=False)           # jami (chegirmasiz)
    discount = Column(Numeric(12, 2), default=0)                # chegirma summasi
    discount_percentage = Column(Numeric(5, 2), default=0)      # chegirma foizi
    total_amount = Column(Numeric(12, 2), nullable=False)       # umumiy summa
    paid_amount = Column(Numeric(12, 2), nullable=False)        # to'langan summa
    change_amount = Column(Numeric(12, 2), default=0)           # qaytim
    debt_amount = Column(Numeric(12, 2), default=0)             # qarzdorlik summasi
    
    # To'lov ma'lumotlari
    payment_method = Column(SAEnum(PaymentMethod), default=PaymentMethod.CASH, nullable=False)
    payment_status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PAID, nullable=False)
    payment_type = Column(SAEnum(PaymentType), default=PaymentType.SERVICE, nullable=True)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Chek va hisob-faktura
    receipt_number = Column(String(50), unique=True, nullable=False, index=True)  # chek raqami
    invoice_number = Column(String(50), unique=True, nullable=True, index=True)    # hisob-faktura raqami
    
    # Qaytarish ma'lumotlari
    refund_amount = Column(Numeric(12, 2), default=0)
    refund_reason = Column(Text, nullable=True)
    refund_date = Column(DateTime(timezone=True), nullable=True)
    refund_receipt_number = Column(String(50), nullable=True)
    
    # Qo'shimcha ma'lumotlar
    notes = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # metadata o'rniga extra_data (metadata rezerv qilingan)
    
    # Online to'lov uchun
    transaction_id = Column(String(255), nullable=True, index=True)
    payment_provider = Column(String(50), nullable=True)  # payme, click, stripe, etc.
    payment_url = Column(String(500), nullable=True)
    
    # Audit
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    clinic = relationship("Clinic", back_populates="payments")
    patient = relationship("Patient", back_populates="payments")
    appointment = relationship("Appointment", back_populates="payment")
    cashier = relationship("User", foreign_keys=[cashier_id], back_populates="payments")
    verifier = relationship("User", foreign_keys=[verified_by])
    
    # ==================== Methods ====================
    
    def calculate_total(self):
        """Umumiy summani hisoblash"""
        # Chegirma foizi bo'yicha hisoblash
        if self.discount_percentage and self.discount_percentage > 0:
            discount_amount = float(self.subtotal) * (float(self.discount_percentage) / 100)
            self.discount = discount_amount
            self.total_amount = float(self.subtotal) - discount_amount
        else:
            self.total_amount = float(self.subtotal) - float(self.discount)
        
        # Qarzdorlikni hisoblash
        self.debt_amount = self.total_amount - self.paid_amount
        if self.debt_amount < 0:
            self.change_amount = abs(self.debt_amount)
            self.debt_amount = 0
        else:
            self.change_amount = 0
        
        # To'lov holatini aniqlash
        if self.paid_amount >= self.total_amount:
            self.payment_status = PaymentStatus.PAID
            self.change_amount = self.paid_amount - self.total_amount
        elif self.paid_amount > 0:
            self.payment_status = PaymentStatus.PARTIAL
        else:
            self.payment_status = PaymentStatus.DEBT
    
    def generate_receipt_number(self):
        """Chek raqamini yaratish"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        time_str = datetime.now().strftime("%H%M%S")
        self.receipt_number = f"RCP-{self.clinic_id}-{date_str}-{time_str}-{self.id}"
    
    def generate_invoice_number(self):
        """Hisob-faktura raqamini yaratish"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m")
        self.invoice_number = f"INV-{self.clinic_id}-{date_str}-{self.id}"
    
    def mark_as_refunded(self, amount: float = None, reason: str = None):
        """To'lovni qaytarish"""
        self.payment_status = PaymentStatus.REFUNDED
        self.refund_date = datetime.now()
        if amount:
            self.refund_amount = amount
        if reason:
            self.refund_reason = reason
        
        # Qaytarish chek raqamini yaratish
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        time_str = datetime.now().strftime("%H%M%S")
        self.refund_receipt_number = f"REF-{self.clinic_id}-{date_str}-{time_str}"
    
    def add_payment(self, amount: float):
        """Qo'shimcha to'lov qilish"""
        self.paid_amount += amount
        self.calculate_total()
    
    def get_services_list(self) -> list:
        """Xizmatlar ro'yxatini olish"""
        return self.services_snapshot or []
    
    def get_total_services_count(self) -> int:
        """Xizmatlar sonini olish"""
        services = self.get_services_list()
        return sum(s.get('qty', 1) for s in services)
    
    def get_service_names(self) -> str:
        """Xizmat nomlarini string sifatida olish"""
        services = self.get_services_list()
        return ", ".join([s.get('service_name', '') for s in services])
    
    def is_completed(self) -> bool:
        """To'lov tugallanganligini tekshirish"""
        return self.payment_status == PaymentStatus.PAID
    
    def is_partial(self) -> bool:
        """Qisman to'langanligini tekshirish"""
        return self.payment_status == PaymentStatus.PARTIAL
    
    def has_debt(self) -> bool:
        """Qarzdorlik mavjudligini tekshirish"""
        return self.debt_amount > 0
    
    def get_debt_amount(self) -> float:
        """Qarzdorlik summasini olish"""
        return float(self.debt_amount)
    
    def to_dict(self) -> dict:
        """Ob'ektni dictionary ga o'zgartirish"""
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "cashier_id": self.cashier_id,
            "services_snapshot": self.services_snapshot,
            "subtotal": float(self.subtotal),
            "discount": float(self.discount),
            "discount_percentage": float(self.discount_percentage),
            "total_amount": float(self.total_amount),
            "paid_amount": float(self.paid_amount),
            "change_amount": float(self.change_amount),
            "debt_amount": float(self.debt_amount),
            "payment_method": self.payment_method.value if self.payment_method else None,
            "payment_status": self.payment_status.value if self.payment_status else None,
            "payment_type": self.payment_type.value if self.payment_type else None,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "receipt_number": self.receipt_number,
            "invoice_number": self.invoice_number,
            "refund_amount": float(self.refund_amount),
            "refund_reason": self.refund_reason,
            "refund_date": self.refund_date.isoformat() if self.refund_date else None,
            "notes": self.notes,
            "extra_data": self.extra_data,
            "transaction_id": self.transaction_id,
            "payment_provider": self.payment_provider,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Payment {self.id}: {self.receipt_number} - {self.total_amount}>"