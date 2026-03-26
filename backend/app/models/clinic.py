from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime


# ✅ Subscription Plan (tariflar)
class SubscriptionPlan(str, enum.Enum):
    TRIAL = "trial"        # sinov davri
    BASIC = "basic"        # 1-5 doctor
    STANDARD = "standard"  # 6-15 doctor
    PREMIUM = "premium"    # unlimited


# ✅ Subscription Status (holat)
class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


# ✅ Clinic Type (klinika turi)
class ClinicType(str, enum.Enum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    DENTAL = "dental"
    LABORATORY = "laboratory"
    DIAGNOSTIC = "diagnostic"
    REHABILITATION = "rehabilitation"
    OTHER = "other"


class Clinic(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clinics"

    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ Asosiy ma'lumotlar
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)
    
    # ✅ Klinika turi
    clinic_type = Column(SAEnum(ClinicType), default=ClinicType.CLINIC, nullable=False)
    
    # ✅ Ish vaqtlari
    working_hours_start = Column(String(5), default="09:00")
    working_hours_end = Column(String(5), default="18:00")
    break_start = Column(String(5), default="13:00")
    break_end = Column(String(5), default="14:00")
    working_days = Column(JSON, default=[1, 2, 3, 4, 5])  # 1=Monday, 7=Sunday
    
    # ✅ Obuna ma'lumotlari
    subscription_plan = Column(
        SAEnum(SubscriptionPlan),
        default=SubscriptionPlan.TRIAL,
        nullable=False
    )
    subscription_status = Column(
        SAEnum(SubscriptionStatus),
        default=SubscriptionStatus.TRIAL,
        nullable=False
    )
    subscription_start = Column(DateTime(timezone=True), nullable=True)
    subscription_end = Column(DateTime(timezone=True), nullable=True)
    subscription_trial_ends = Column(DateTime(timezone=True), nullable=True)
    monthly_price = Column(Numeric(12, 2), default=0)
    yearly_price = Column(Numeric(12, 2), default=0)
    setup_fee = Column(Numeric(12, 2), default=0)
    
    # ✅ Limitlar
    max_doctors = Column(Integer, default=5)
    max_staff = Column(Integer, default=10)
    max_patients = Column(Integer, default=1000)
    max_appointments_per_day = Column(Integer, default=50)
    storage_limit_mb = Column(Integer, default=100)
    
    # ✅ Faollik
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # ✅ Statistika
    rating = Column(Numeric(3, 2), default=0)
    total_reviews = Column(Integer, default=0)
    total_doctors = Column(Integer, default=0)
    total_staff = Column(Integer, default=0)
    total_patients = Column(Integer, default=0)
    total_appointments = Column(Integer, default=0)
    total_revenue = Column(Numeric(12, 2), default=0)
    
    # ✅ Qo'shimcha
    settings = Column(JSON, default={})  # Klinika sozlamalari
    features = Column(JSON, default=[])  # Aktiv xususiyatlar
    tags = Column(JSON, default=[])      # Teglar
    
    # ✅ Payment ma'lumotlari
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    payment_method_id = Column(String(255), nullable=True)
    auto_renew = Column(Boolean, default=True)
    
    # ✅ Xavfsizlik
    api_key = Column(String(255), nullable=True, unique=True)
    webhook_url = Column(String(500), nullable=True)
    
    # ✅ Relationships
    users = relationship("User", back_populates="clinic", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="clinic", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="clinic", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="clinic", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="clinic", cascade="all, delete-orphan")
    medical_records = relationship("MedicalRecord", back_populates="clinic", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="clinic", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="clinic", cascade="all, delete-orphan")
    
    # ✅ Methods
    def is_subscription_active(self) -> bool:
        """Obuna aktivligini tekshirish"""
        if self.subscription_status != SubscriptionStatus.ACTIVE:
            return False
        if self.subscription_end and self.subscription_end < datetime.now():
            return False
        return True
    
    def is_trial_active(self) -> bool:
        """Trial davri aktivligini tekshirish"""
        if self.subscription_plan != SubscriptionPlan.TRIAL:
            return False
        if self.subscription_trial_ends and self.subscription_trial_ends < datetime.now():
            return False
        return True
    
    def get_remaining_trial_days(self) -> int:
        """Qolgan trial kunlarini olish"""
        if not self.subscription_trial_ends:
            return 0
        remaining = (self.subscription_trial_ends - datetime.now()).days
        return max(0, remaining)
    
    def can_add_doctor(self) -> bool:
        """Yangi shifokor qo'sha olish imkoniyatini tekshirish"""
        if not self.is_subscription_active() and not self.is_trial_active():
            return False
        return self.total_doctors < self.max_doctors
    
    def can_add_staff(self) -> bool:
        """Yangi xodim qo'sha olish imkoniyatini tekshirish"""
        if not self.is_subscription_active() and not self.is_trial_active():
            return False
        return self.total_staff < self.max_staff
    
    def can_add_patient(self) -> bool:
        """Yangi bemor qo'sha olish imkoniyatini tekshirish"""
        if not self.is_subscription_active() and not self.is_trial_active():
            return False
        return self.total_patients < self.max_patients
    
    def update_statistics(self):
        """Statistikani yangilash"""
        # Doktorlar soni
        self.total_doctors = len([u for u in self.users if u.role == "doctor"])
        # Xodimlar soni
        self.total_staff = len([u for u in self.users if u.role in ["staff", "reception"]])
        # Bemorlar soni
        self.total_patients = self.patients.count()
        # Uchrashuvlar soni
        self.total_appointments = self.appointments.count()
    
    def __repr__(self):
        return f"<Clinic {self.name}>"