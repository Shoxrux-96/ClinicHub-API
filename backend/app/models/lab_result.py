from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin
import enum
from sqlalchemy import Enum as SAEnum

class LabResultStatus(str, enum.Enum):
    PENDING = "pending"       # kutilmoqda
    READY = "ready"           # tayyor
    DELIVERED = "delivered"   # berildi

class LabResult(Base, TimestampMixin):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # yuborgan doctor
    entered_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # kiritgan reception/doctor

    test_name = Column(String(255), nullable=False)   # tahlil nomi
    test_category = Column(String(100), nullable=True) # toifa (qon, siydik, ...)

    # Natijalar — oddiy yoki murakkab (JSON)
    results = Column(JSON, nullable=True)  # [{"name": "Gemoglobin", "value": "130", "unit": "g/L", "reference": "120-160"}]
    file_path = Column(String(500), nullable=True)  # yuklangan PDF fayl

    status = Column(SAEnum(LabResultStatus), default=LabResultStatus.PENDING)
    notes = Column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="lab_results")
    
    # User bilan aloqalar (foreign_keys aniq ko‘rsatiladi)
    entered_by_user = relationship(
        "User",
        foreign_keys=[entered_by],
        back_populates="lab_results_entered"
    )
    doctor = relationship(
        "User",
        foreign_keys=[doctor_id],
        back_populates="lab_results_doctor"
    )