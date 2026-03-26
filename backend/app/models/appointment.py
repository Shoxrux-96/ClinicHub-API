from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Text, DateTime, Boolean, Float, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime, date, timedelta


class AppointmentStatus(str, enum.Enum):
    """Uchrashuv holati"""
    WAITING = "waiting"           # kutmoqda
    IN_PROGRESS = "in_progress"   # qabulda
    COMPLETED = "completed"       # tugallandi
    CANCELLED = "cancelled"       # bekor qilindi
    NO_SHOW = "no_show"           # kelmadi
    CONFIRMED = "confirmed"       # tasdiqlangan
    RESCHEDULED = "rescheduled"   # vaqti o'zgartirilgan


class AppointmentType(str, enum.Enum):
    """Uchrashuv turi"""
    CONSULTATION = "consultation"      # konsultatsiya
    FOLLOW_UP = "follow_up"            # nazorat
    CHECKUP = "checkup"                # tekshiruv
    EMERGENCY = "emergency"            # tez yordam
    VACCINATION = "vaccination"        # emlash
    PROCEDURE = "procedure"            # muolaja
    LAB_TEST = "lab_test"              # laboratoriya
    SURGERY = "surgery"                # jarrohlik
    OTHER = "other"                    # boshqa


class AppointmentPriority(str, enum.Enum):
    """Uchrashuv prioriteti"""
    LOW = "low"          # past
    NORMAL = "normal"    # normal
    HIGH = "high"        # yuqori
    URGENT = "urgent"    # shoshilinch


class Appointment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "appointments"
    
    # Indekslar
    __table_args__ = (
        Index('idx_appointment_clinic_date', 'clinic_id', 'appointment_date'),
        Index('idx_appointment_doctor_date', 'doctor_id', 'appointment_date'),
        Index('idx_appointment_patient_date', 'patient_id', 'appointment_date'),
        Index('idx_appointment_status', 'status'),
        Index('idx_appointment_priority', 'priority'),
    )

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reception_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Uchrashuv vaqti
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(Time, nullable=True)
    duration = Column(Integer, default=30)  # daqiqalarda
    end_time = Column(Time, nullable=True)
    queue_number = Column(Integer, nullable=False)  # navbat raqami
    
    # Uchrashuv ma'lumotlari
    type = Column(SAEnum(AppointmentType), default=AppointmentType.CONSULTATION, nullable=True)
    priority = Column(SAEnum(AppointmentPriority), default=AppointmentPriority.NORMAL, nullable=True)
    status = Column(SAEnum(AppointmentStatus), default=AppointmentStatus.WAITING, nullable=False)
    
    # Bemor ma'lumotlari
    visit_reason = Column(Text, nullable=True)  # kelish sababi
    symptoms = Column(Text, nullable=True)      # simptomlar
    notes = Column(Text, nullable=True)         # qo'shimcha izohlar
    
    # Shifokor ma'lumotlari
    diagnosis = Column(Text, nullable=True)      # tashxis
    prescription = Column(Text, nullable=True)  # retsept
    follow_up_date = Column(Date, nullable=True) # keyingi qabul sanasi
    
    # Vaqt belgilari
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_reason = Column(Text, nullable=True)
    
    # Xizmatlar va to'lov
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    payment_status = Column(String(20), default="pending")  # pending, paid, partially_paid
    
    # Qo'shimcha
    is_online = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    waiting_number = Column(Integer, nullable=True)

    # Relationships
    clinic = relationship("Clinic", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship(
        "User", 
        foreign_keys=[doctor_id], 
        back_populates="appointments_as_doctor"
    )
    reception = relationship(
        "User", 
        foreign_keys=[reception_id], 
        back_populates="appointments_as_reception"
    )
    service = relationship("Service", back_populates="appointments")
    medical_record = relationship(
        "MedicalRecord", 
        back_populates="appointment", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    payment = relationship(
        "Payment", 
        back_populates="appointment", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # ==================== Methods ====================
    
    def calculate_end_time(self):
        """Tugash vaqtini hisoblash"""
        if self.appointment_time and self.duration:
            start = datetime.combine(date.today(), self.appointment_time)
            end = start + timedelta(minutes=self.duration)
            self.end_time = end.time()
    
    def check_in(self):
        """Check-in qilish"""
        self.status = AppointmentStatus.IN_PROGRESS
        self.checked_in_at = datetime.now()
    
    def start(self):
        """Uchrashuvni boshlash"""
        self.status = AppointmentStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def complete(self):
        """Uchrashuvni tugatish"""
        self.status = AppointmentStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def cancel(self, reason: str = None):
        """Uchrashuvni bekor qilish"""
        self.status = AppointmentStatus.CANCELLED
        self.cancelled_at = datetime.now()
        self.cancelled_reason = reason
    
    def reschedule(self, new_date: date, new_time: Time):
        """Uchrashuv vaqtini o'zgartirish"""
        self.status = AppointmentStatus.RESCHEDULED
        self.appointment_date = new_date
        self.appointment_time = new_time
        self.calculate_end_time()
    
    def mark_no_show(self):
        """Kelmadi deb belgilash"""
        self.status = AppointmentStatus.NO_SHOW
        self.completed_at = datetime.now()
    
    def confirm(self):
        """Uchrashuvni tasdiqlash"""
        self.status = AppointmentStatus.CONFIRMED
    
    def set_priority(self, priority: AppointmentPriority):
        """Prioritetni o'rnatish"""
        self.priority = priority
    
    def is_high_priority(self) -> bool:
        """Yuqori prioritetli ekanligini tekshirish"""
        return self.priority in [AppointmentPriority.HIGH, AppointmentPriority.URGENT]
    
    def is_today(self) -> bool:
        """Bugungi uchrashuv ekanligini tekshirish"""
        return self.appointment_date == date.today()
    
    def is_upcoming(self) -> bool:
        """Kelajakdagi uchrashuv ekanligini tekshirish"""
        return self.appointment_date > date.today()
    
    def is_past(self) -> bool:
        """O'tgan uchrashuv ekanligini tekshirish"""
        return self.appointment_date < date.today()
    
    def get_duration_minutes(self) -> int:
        """Davomiylikni daqiqalarda olish"""
        return self.duration or 0
    
    def get_remaining_balance(self) -> float:
        """Qolgan to'lov miqdorini olish"""
        return self.total_amount - self.paid_amount
    
    def is_paid(self) -> bool:
        """To'liq to'langanligini tekshirish"""
        return self.paid_amount >= self.total_amount
    
    def get_queue_position(self) -> int:
        """Navbatdagi o'rnini olish"""
        return self.queue_number
    
    def to_dict(self) -> dict:
        """Ob'ektni dictionary ga o'zgartirish"""
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "reception_id": self.reception_id,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "appointment_time": self.appointment_time.strftime("%H:%M") if self.appointment_time else None,
            "duration": self.duration,
            "queue_number": self.queue_number,
            "type": self.type.value if self.type else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "visit_reason": self.visit_reason,
            "symptoms": self.symptoms,
            "notes": self.notes,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "total_amount": self.total_amount,
            "paid_amount": self.paid_amount,
            "payment_status": self.payment_status,
            "is_online": self.is_online,
            "reminder_sent": self.reminder_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Appointment {self.id}: {self.appointment_date} {self.appointment_time}>"