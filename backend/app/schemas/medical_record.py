from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PrescriptionItem(BaseModel):
    drug_name: str
    dosage: str
    frequency: str
    duration: str
    notes: Optional[str] = None

class MedicalRecordCreate(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    complaint: Optional[str] = None
    anamnesis: Optional[str] = None
    examination: Optional[str] = None
    diagnosis: Optional[str] = None
    diagnosis_code: Optional[str] = None
    treatment: Optional[str] = None
    prescription: Optional[List[PrescriptionItem]] = None
    recommendations: Optional[str] = None
    next_visit_date: Optional[str] = None

class MedicalRecordUpdate(BaseModel):
    complaint: Optional[str] = None
    anamnesis: Optional[str] = None
    examination: Optional[str] = None
    diagnosis: Optional[str] = None
    diagnosis_code: Optional[str] = None
    treatment: Optional[str] = None
    prescription: Optional[List[PrescriptionItem]] = None
    recommendations: Optional[str] = None
    next_visit_date: Optional[str] = None

class MedicalRecordResponse(BaseModel):
    id: int
    clinic_id: int
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int]
    complaint: Optional[str]
    anamnesis: Optional[str]
    examination: Optional[str]
    diagnosis: Optional[str]
    diagnosis_code: Optional[str]
    treatment: Optional[str]
    prescription: Optional[List[PrescriptionItem]]
    recommendations: Optional[str]
    next_visit_date: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True