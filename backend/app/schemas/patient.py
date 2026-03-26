from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ==================== PATIENT ENUMS ====================

class Gender(str, Enum):
    """Jins"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BloodType(str, Enum):
    """Qon guruhi"""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class MaritalStatus(str, Enum):
    """Oilaviy holat"""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"


# ==================== PATIENT BASE SCHEMAS ====================

class PatientBase(BaseModel):
    """Asosiy patient schema"""
    first_name: str = Field(..., min_length=2, max_length=100, description="First name")
    last_name: str = Field(..., min_length=2, max_length=100, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: str = Field(..., max_length=20, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[Gender] = Field(None, description="Gender")
    blood_type: Optional[BloodType] = Field(None, description="Blood type")
    address: Optional[str] = Field(None, max_length=500, description="Address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    occupation: Optional[str] = Field(None, max_length=100, description="Occupation")
    emergency_contact_name: Optional[str] = Field(None, max_length=255, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="Emergency contact phone")
    marital_status: Optional[MaritalStatus] = Field(None, description="Marital status")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    class Config:
        use_enum_values = True


class PatientCreate(PatientBase):
    """Bemor yaratish uchun schema"""
    clinic_id: int = Field(..., description="Clinic ID")
    user_id: Optional[int] = Field(None, description="Associated user ID")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Telefon raqamini tekshirish"""
        if v:
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 9:
                raise ValueError('Phone number must be at least 9 digits')
        return v


class PatientUpdate(BaseModel):
    """Bemor ma'lumotlarini yangilash uchun schema"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_type: Optional[BloodType] = None
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    occupation: Optional[str] = Field(None, max_length=100)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    marital_status: Optional[MaritalStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    
    class Config:
        use_enum_values = True


# ==================== PATIENT RESPONSE SCHEMAS ====================

class PatientResponse(PatientBase):
    """Bemor javob schemasi"""
    id: int
    clinic_id: int
    user_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class PatientDetailResponse(PatientResponse):
    """Bemor batafsil ma'lumotlari"""
    appointments_count: int = Field(default=0, description="Number of appointments")
    completed_appointments: int = Field(default=0, description="Completed appointments")
    cancelled_appointments: int = Field(default=0, description="Cancelled appointments")
    total_spent: float = Field(default=0.0, description="Total amount spent")
    last_visit: Optional[datetime] = Field(None, description="Last visit date")
    clinic_name: Optional[str] = Field(None, description="Clinic name")
    doctor_name: Optional[str] = Field(None, description="Primary doctor name")


class PatientListResponse(BaseModel):
    """Bemorlar ro'yxati javob schemasi"""
    items: List[PatientResponse]
    total: int
    page: int
    size: int
    pages: int


# ==================== PATIENT MEDICAL HISTORY ====================

class Allergy(BaseModel):
    """Allergiya"""
    id: Optional[int] = None
    name: str = Field(..., max_length=255, description="Allergy name")
    severity: str = Field(..., description="Severity (mild, moderate, severe)")
    reaction: Optional[str] = Field(None, description="Reaction description")
    diagnosed_date: Optional[date] = None
    notes: Optional[str] = None


class ChronicCondition(BaseModel):
    """Surunkali kasallik"""
    id: Optional[int] = None
    name: str = Field(..., max_length=255, description="Condition name")
    diagnosed_date: Optional[date] = None
    status: str = Field("active", description="Status (active, controlled, resolved)")
    notes: Optional[str] = None


class Medication(BaseModel):
    """Dori-darmon"""
    id: Optional[int] = None
    name: str = Field(..., max_length=255, description="Medication name")
    dosage: str = Field(..., description="Dosage")
    frequency: str = Field(..., description="Frequency")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None


class VitalSigns(BaseModel):
    """Hayotiy ko'rsatkichlar"""
    id: Optional[int] = None
    date: datetime = Field(default_factory=datetime.now)
    height: Optional[float] = Field(None, description="Height (cm)")
    weight: Optional[float] = Field(None, description="Weight (kg)")
    blood_pressure_systolic: Optional[int] = Field(None, description="Blood pressure systolic")
    blood_pressure_diastolic: Optional[int] = Field(None, description="Blood pressure diastolic")
    heart_rate: Optional[int] = Field(None, description="Heart rate (bpm)")
    temperature: Optional[float] = Field(None, description="Temperature (C)")
    respiratory_rate: Optional[int] = Field(None, description="Respiratory rate")
    oxygen_saturation: Optional[int] = Field(None, description="Oxygen saturation (%)")
    notes: Optional[str] = None


class MedicalRecord(BaseModel):
    """Tibbiy yozuv"""
    id: Optional[int] = None
    date: datetime = Field(default_factory=datetime.now)
    type: str = Field(..., description="Record type (diagnosis, prescription, procedure, etc.)")
    title: str = Field(..., max_length=255, description="Record title")
    description: str = Field(..., description="Record description")
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    attachments: List[str] = Field(default_factory=list, description="Attached files")
    notes: Optional[str] = None


class PatientMedicalHistory(BaseModel):
    """Bemorning tibbiy tarixi"""
    patient_id: int
    patient_name: str
    allergies: List[Allergy] = Field(default_factory=list)
    chronic_conditions: List[ChronicCondition] = Field(default_factory=list)
    current_medications: List[Medication] = Field(default_factory=list)
    past_medications: List[Medication] = Field(default_factory=list)
    vital_signs: List[VitalSigns] = Field(default_factory=list)
    medical_records: List[MedicalRecord] = Field(default_factory=list)
    surgical_history: List[str] = Field(default_factory=list)
    family_history: Optional[str] = None
    social_history: Optional[str] = None


# ==================== PATIENT FILTERS ====================

class PatientFilter(BaseModel):
    """Bemor filtrlari"""
    first_name: Optional[str] = Field(None, description="Filter by first name")
    last_name: Optional[str] = Field(None, description="Filter by last name")
    phone: Optional[str] = Field(None, description="Filter by phone")
    email: Optional[str] = Field(None, description="Filter by email")
    gender: Optional[Gender] = None
    blood_type: Optional[BloodType] = None
    city: Optional[str] = None
    clinic_id: Optional[int] = None
    is_active: Optional[bool] = None
    date_of_birth_from: Optional[date] = None
    date_of_birth_to: Optional[date] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


# ==================== PATIENT STATISTICS ====================

class PatientStats(BaseModel):
    """Bemorlar statistikasi"""
    total_patients: int
    active_patients: int
    inactive_patients: int
    new_patients_today: int
    new_patients_this_week: int
    new_patients_this_month: int
    patients_by_gender: dict = Field(default_factory=dict)
    patients_by_age_group: dict = Field(default_factory=dict)
    patients_by_blood_type: dict = Field(default_factory=dict)
    most_common_allergies: List[dict] = Field(default_factory=list)
    most_common_conditions: List[dict] = Field(default_factory=list)


# ==================== EMERGENCY CONTACT ====================

class EmergencyContact(BaseModel):
    """Favqulodda aloqa"""
    name: str = Field(..., max_length=255)
    relationship: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None


# ==================== VALIDATION FUNCTIONS ====================

def calculate_age(date_of_birth: date) -> int:
    """
    Yoshni hisoblash
    
    Args:
        date_of_birth: Tug'ilgan sana
        
    Returns:
        int: Yosh
    """
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def get_age_group(age: int) -> str:
    """
    Yosh guruhini aniqlash
    
    Args:
        age: Yosh
        
    Returns:
        str: Yosh guruhi
    """
    if age < 1:
        return "infant"
    elif age < 3:
        return "toddler"
    elif age < 6:
        return "preschool"
    elif age < 12:
        return "child"
    elif age < 18:
        return "teenager"
    elif age < 35:
        return "young_adult"
    elif age < 50:
        return "adult"
    elif age < 65:
        return "middle_age"
    else:
        return "senior"