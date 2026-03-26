from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class BloodType(str, enum.Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "unknown"

class Patient(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    
    full_name = Column(String(255), nullable=False)
    birth_date = Column(Date, nullable=True)
    gender = Column(SAEnum(Gender), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    
    # Tibbiy ma'lumotlar
    blood_type = Column(SAEnum(BloodType), default=BloodType.UNKNOWN)
    allergies = Column(Text, nullable=True)
    chronic_diseases = Column(Text, nullable=True)
    
    # Bemor raqami (klinika ichida unikal)
    patient_code = Column(String(20), nullable=True, index=True)

    # Relationships
    clinic = relationship("Clinic", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    lab_results = relationship("LabResult", back_populates="patient")
    payments = relationship("Payment", back_populates="patient")