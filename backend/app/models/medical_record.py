from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime


class RecordType(str, enum.Enum):
    """Yozuv turi"""
    DIAGNOSIS = "diagnosis"          # Tashxis
    PRESCRIPTION = "prescription"    # Retsept
    PROCEDURE = "procedure"          # Muolaja
    EXAMINATION = "examination"      # Ko'rik
    LAB_RESULT = "lab_result"        # Laboratoriya natijasi
    FOLLOW_UP = "follow_up"          # Nazorat
    OTHER = "other"                  # Boshqa


class MedicalRecord(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "medical_records"
    
    # Indekslar
    __table_args__ = (
        Index('idx_medical_record_patient', 'patient_id'),
        Index('idx_medical_record_doctor', 'doctor_id'),
        Index('idx_medical_record_clinic', 'clinic_id'),
        Index('idx_medical_record_date', 'record_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, unique=True, index=True)
    
    # Yozuv turi
    record_type = Column(SAEnum(RecordType), default=RecordType.DIAGNOSIS, nullable=True)
    
    # Tibbiy ma'lumotlar
    complaint = Column(Text, nullable=True)        # shikoyat
    anamnesis = Column(Text, nullable=True)        # kasallik tarixi
    examination = Column(Text, nullable=True)      # ko'rik natijasi
    diagnosis = Column(Text, nullable=True)        # tashxis
    diagnosis_code = Column(String(20), nullable=True, index=True)  # ICD-10 kodi
    treatment = Column(Text, nullable=True)        # davolash
    prescription = Column(JSON, nullable=True)     # retsept (dorilar ro'yxati JSON)
    recommendations = Column(Text, nullable=True)  # tavsiyalar
    
    # Vaqt
    record_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    next_visit_date = Column(String(50), nullable=True)  # keyingi ko'rik sanasi
    
    # Qo'shimcha ma'lumotlar
    notes = Column(Text, nullable=True)            # qo'shimcha izohlar
    attachments = Column(JSON, nullable=True)      # biriktirilgan fayllar (rasm, hujjat, etc.)
    is_confidential = Column(Boolean, default=False)  # maxfiy ma'lumot
    is_follow_up = Column(Boolean, default=False)     # nazorat yozuvi
    
    # Vital signs (hayotiy ko'rsatkichlar)
    blood_pressure = Column(String(20), nullable=True)  # qon bosimi (120/80)
    heart_rate = Column(Integer, nullable=True)         # yurak urishi
    temperature = Column(String(10), nullable=True)     # tana harorati
    weight = Column(String(10), nullable=True)          # vazn (kg)
    height = Column(String(10), nullable=True)          # bo'y (cm)
    bmi = Column(String(10), nullable=True)             # BMI

    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="medical_records")
    clinic = relationship("Clinic", back_populates="medical_records")
    appointment = relationship("Appointment", back_populates="medical_record")
    
    # ==================== Methods ====================
    
    def calculate_bmi(self):
        """BMI ni hisoblash"""
        if self.weight and self.height:
            try:
                weight = float(self.weight)
                height = float(self.height) / 100  # cm to m
                if height > 0:
                    bmi = weight / (height * height)
                    self.bmi = f"{bmi:.1f}"
            except (ValueError, TypeError):
                pass
    
    def set_vital_signs(self, bp: str = None, hr: int = None, temp: str = None, 
                         w: str = None, h: str = None):
        """Hayotiy ko'rsatkichlarni o'rnatish"""
        if bp:
            self.blood_pressure = bp
        if hr:
            self.heart_rate = hr
        if temp:
            self.temperature = temp
        if w:
            self.weight = w
        if h:
            self.height = h
            self.calculate_bmi()
    
    def add_attachment(self, file_url: str, file_name: str, file_type: str):
        """Fayl biriktirish"""
        if not self.attachments:
            self.attachments = []
        self.attachments.append({
            "url": file_url,
            "name": file_name,
            "type": file_type,
            "uploaded_at": datetime.now().isoformat()
        })
    
    def add_prescription(self, medication: str, dosage: str, frequency: str, duration: str):
        """Retsept qo'shish"""
        if not self.prescription:
            self.prescription = []
        self.prescription.append({
            "medication": medication,
            "dosage": dosage,
            "frequency": frequency,
            "duration": duration,
            "prescribed_at": datetime.now().isoformat()
        })
    
    def get_diagnosis_code_display(self) -> str:
        """Tashxis kodini formatlash"""
        if self.diagnosis_code:
            return f"{self.diagnosis_code} - {self.diagnosis}"
        return self.diagnosis or ""
    
    def get_prescription_list(self) -> list:
        """Retseptlar ro'yxatini olish"""
        return self.prescription or []
    
    def get_attachments_list(self) -> list:
        """Biriktirilgan fayllar ro'yxatini olish"""
        return self.attachments or []
    
    def has_prescription(self) -> bool:
        """Retsept mavjudligini tekshirish"""
        return bool(self.prescription and len(self.prescription) > 0)
    
    def has_attachments(self) -> bool:
        """Biriktirilgan fayllar mavjudligini tekshirish"""
        return bool(self.attachments and len(self.attachments) > 0)
    
    def to_dict(self) -> dict:
        """Ob'ektni dictionary ga o'zgartirish"""
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "appointment_id": self.appointment_id,
            "record_type": self.record_type.value if self.record_type else None,
            "complaint": self.complaint,
            "anamnesis": self.anamnesis,
            "examination": self.examination,
            "diagnosis": self.diagnosis,
            "diagnosis_code": self.diagnosis_code,
            "treatment": self.treatment,
            "prescription": self.prescription,
            "recommendations": self.recommendations,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "next_visit_date": self.next_visit_date,
            "notes": self.notes,
            "attachments": self.attachments,
            "is_confidential": self.is_confidential,
            "is_follow_up": self.is_follow_up,
            "blood_pressure": self.blood_pressure,
            "heart_rate": self.heart_rate,
            "temperature": self.temperature,
            "weight": self.weight,
            "height": self.height,
            "bmi": self.bmi,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<MedicalRecord {self.id}: Patient {self.patient_id} - {self.diagnosis}>"