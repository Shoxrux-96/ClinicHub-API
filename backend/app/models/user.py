from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum


class UserRole(str, enum.Enum):
    """Foydalanuvchi rollari"""
    OWNER = "owner"
    ADMIN = "admin"
    DOCTOR = "doctor"
    RECEPTION = "reception"
    STAFF = "staff"
    PATIENT = "patient"


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True)  # owner uchun NULL
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.STAFF)
    
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    
    # Doctor uchun qo'shimcha
    specialization = Column(String(255), nullable=True)  # mutaxassislik
    room_number = Column(String(20), nullable=True)       # xona raqami
    
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    clinic = relationship("Clinic", back_populates="users")

    # Appointment relationshiplar
    appointments_as_doctor = relationship(
        "Appointment",
        foreign_keys="Appointment.doctor_id",
        back_populates="doctor",
        cascade="all, delete-orphan"
    )
    appointments_as_reception = relationship(
        "Appointment",
        foreign_keys="Appointment.reception_id",
        back_populates="reception",
        cascade="all, delete-orphan"
    )

    # Medical Records
    medical_records = relationship("MedicalRecord", back_populates="doctor", cascade="all, delete-orphan")

    # Lab Results relationshiplar
    lab_results_entered = relationship(
        "LabResult",
        foreign_keys="LabResult.entered_by",
        back_populates="entered_by_user",
        cascade="all, delete-orphan"
    )
    lab_results_doctor = relationship(
        "LabResult",
        foreign_keys="LabResult.doctor_id",
        back_populates="doctor_user",
        cascade="all, delete-orphan"
    )
    
    # Notifications
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    # Payments
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")