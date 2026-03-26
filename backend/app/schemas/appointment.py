from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum


# ==================== APPOINTMENT ENUMS ====================

class AppointmentStatus(str, Enum):
    """Uchrashuv holati"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"
    WAITING = "waiting"


class AppointmentType(str, Enum):
    """Uchrashuv turi"""
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    CHECKUP = "checkup"
    EMERGENCY = "emergency"
    VACCINATION = "vaccination"
    SURGERY = "surgery"
    LAB_TEST = "lab_test"
    PROCEDURE = "procedure"
    OTHER = "other"


class AppointmentPriority(str, Enum):
    """Uchrashuv prioriteti"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ==================== APPOINTMENT BASE SCHEMAS ====================

class AppointmentBase(BaseModel):
    """Asosiy appointment schema"""
    patient_id: int = Field(..., description="Patient ID")
    doctor_id: int = Field(..., description="Doctor ID")
    clinic_id: int = Field(..., description="Clinic ID")
    appointment_date: date = Field(..., description="Appointment date")
    appointment_time: str = Field(..., description="Appointment time (HH:MM)")
    duration: int = Field(30, ge=15, le=240, description="Duration in minutes")
    type: AppointmentType = Field(AppointmentType.CONSULTATION, description="Appointment type")
    priority: AppointmentPriority = Field(AppointmentPriority.NORMAL, description="Priority")
    status: AppointmentStatus = Field(AppointmentStatus.SCHEDULED, description="Status")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for visit")
    symptoms: Optional[str] = Field(None, max_length=1000, description="Symptoms")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    class Config:
        use_enum_values = True


class AppointmentCreate(AppointmentBase):
    """Uchrashuv yaratish uchun schema"""
    created_by: Optional[int] = Field(None, description="Created by user ID")
    
    @validator('appointment_time')
    def validate_time(cls, v):
        """Vaqt formatini tekshirish"""
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError('Time must be in HH:MM format')
        return v


class AppointmentUpdate(BaseModel):
    """Uchrashuv ma'lumotlarini yangilash uchun schema"""
    appointment_date: Optional[date] = None
    appointment_time: Optional[str] = None
    duration: Optional[int] = Field(None, ge=15, le=240)
    type: Optional[AppointmentType] = None
    priority: Optional[AppointmentPriority] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = Field(None, max_length=500)
    symptoms: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)
    diagnosis: Optional[str] = Field(None, max_length=1000)
    prescription: Optional[str] = Field(None, max_length=1000)
    follow_up_date: Optional[date] = None
    
    class Config:
        use_enum_values = True


# ==================== APPOINTMENT RESPONSE SCHEMAS ====================

class AppointmentResponse(AppointmentBase):
    """Uchrashuv javob schemasi"""
    id: int
    created_by: Optional[int] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class AppointmentDetailResponse(AppointmentResponse):
    """Uchrashuv batafsil ma'lumotlari"""
    patient_name: str = Field(..., description="Patient full name")
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    doctor_name: str = Field(..., description="Doctor full name")
    doctor_specialization: Optional[str] = None
    clinic_name: str = Field(..., description="Clinic name")
    clinic_address: Optional[str] = None
    waiting_number: Optional[int] = None
    estimated_wait_time: Optional[int] = Field(None, description="Estimated wait time in minutes")


class AppointmentListResponse(BaseModel):
    """Uchrashuvlar ro'yxati javob schemasi"""
    items: List[AppointmentResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== APPOINTMENT STATISTICS ====================

class AppointmentStatistics(BaseModel):
    """Uchrashuv statistikasi"""
    total_appointments: int
    scheduled: int
    confirmed: int
    completed: int
    cancelled: int
    no_show: int
    rescheduled: int
    today_appointments: int
    tomorrow_appointments: int
    this_week_appointments: int
    this_month_appointments: int
    average_duration: float
    average_wait_time: float
    appointments_by_type: dict = Field(default_factory=dict)
    appointments_by_doctor: List[dict] = Field(default_factory=list)
    peak_hours: List[dict] = Field(default_factory=list)
    completion_rate: float


# ==================== APPOINTMENT FILTERS ====================

class AppointmentFilter(BaseModel):
    """Uchrashuv filtrlari"""
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    clinic_id: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    type: Optional[AppointmentType] = None
    priority: Optional[AppointmentPriority] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    time_from: Optional[str] = None
    time_to: Optional[str] = None
    search: Optional[str] = Field(None, description="Search by patient or doctor name")
    
    class Config:
        use_enum_values = True


# ==================== TIME SLOTS ====================

class TimeSlot(BaseModel):
    """Vaqt oralig'i"""
    time: str = Field(..., description="Time (HH:MM)")
    is_available: bool = True
    appointment_id: Optional[int] = None


class DoctorSchedule(BaseModel):
    """Shifokor jadvali"""
    doctor_id: int
    doctor_name: str
    date: date
    working_hours_start: str
    working_hours_end: str
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    time_slots: List[TimeSlot] = Field(default_factory=list)
    available_slots: int = 0
    total_slots: int = 0


# ==================== APPOINTMENT REMINDER ====================

class AppointmentReminder(BaseModel):
    """Uchrashuv eslatmasi"""
    appointment_id: int
    patient_id: int
    patient_name: str
    patient_phone: str
    patient_email: Optional[str] = None
    doctor_name: str
    clinic_name: str
    appointment_date: date
    appointment_time: str
    reminder_time: datetime
    reminder_type: str = Field(..., description="sms, email, push")
    reminder_sent: bool = False
    sent_at: Optional[datetime] = None


# ==================== APPOINTMENT FEEDBACK ====================

class AppointmentFeedback(BaseModel):
    """Uchrashuv feedback"""
    appointment_id: int
    patient_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    comment: Optional[str] = Field(None, max_length=1000)
    waiting_time_rating: Optional[int] = Field(None, ge=1, le=5)
    doctor_communication_rating: Optional[int] = Field(None, ge=1, le=5)
    facility_rating: Optional[int] = Field(None, ge=1, le=5)
    created_at: datetime


# ==================== APPOINTMENT BULK OPERATIONS ====================

class AppointmentBulkCreate(BaseModel):
    """Bir nechta uchrashuv yaratish"""
    appointments: List[AppointmentCreate]
    clinic_id: int


class AppointmentBulkResponse(BaseModel):
    """Bir nechta uchrashuv yaratish javobi"""
    created: List[AppointmentResponse]
    failed: List[dict]
    total_created: int
    total_failed: int


# ==================== APPOINTMENT EXPORT ====================

class AppointmentExport(BaseModel):
    """Uchrashuvlarni eksport qilish"""
    filters: AppointmentFilter
    format: str = Field("csv", description="Export format (csv, excel, pdf)")
    fields: List[str] = Field(default_factory=list, description="Fields to export")
    date_range: Optional[str] = None


# ==================== VALIDATION FUNCTIONS ====================

def is_time_slot_available(
    appointment_time: str,
    duration: int,
    existing_appointments: List[dict]
) -> bool:
    """
    Vaqt oralig'ini tekshirish
    
    Args:
        appointment_time: Uchrashuv vaqti
        duration: Davomiyligi (daqiqa)
        existing_appointments: Mavjud uchrashuvlar
        
    Returns:
        bool: Vaqt oralig'i bo'sh bo'lsa True
    """
    start_time = datetime.strptime(appointment_time, "%H:%M")
    end_time = start_time + timedelta(minutes=duration)
    
    for apt in existing_appointments:
        apt_start = datetime.strptime(apt["appointment_time"], "%H:%M")
        apt_end = apt_start + timedelta(minutes=apt["duration"])
        
        # Vaqt oralig'ining ustma-ust tushishini tekshirish
        if not (end_time <= apt_start or start_time >= apt_end):
            return False
    
    return True


def get_next_available_slot(
    working_hours_start: str,
    working_hours_end: str,
    duration: int,
    existing_appointments: List[dict],
    break_start: Optional[str] = None,
    break_end: Optional[str] = None
) -> Optional[str]:
    """
    Keyingi bo'sh vaqt oralig'ini topish
    
    Returns:
        Optional[str]: Bo'sh vaqt yoki None
    """
    from datetime import timedelta
    
    start = datetime.strptime(working_hours_start, "%H:%M")
    end = datetime.strptime(working_hours_end, "%H:%M")
    
    current = start
    
    while current + timedelta(minutes=duration) <= end:
        time_str = current.strftime("%H:%M")
        
        # Tanaffus vaqtini tekshirish
        if break_start and break_end:
            break_start_time = datetime.strptime(break_start, "%H:%M")
            break_end_time = datetime.strptime(break_end, "%H:%M")
            
            if break_start_time <= current < break_end_time:
                current = break_end_time
                continue
        
        # Uchrashuvlar bilan ustma-ust tushishini tekshirish
        if is_time_slot_available(time_str, duration, existing_appointments):
            return time_str
        
        current += timedelta(minutes=30)  # 30 daqiqalik qadam
    
    return None


# Import for timedelta
from datetime import timedelta