from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.lab_result import LabResultStatus

class LabResultItem(BaseModel):
    name: str           # ko'rsatkich nomi
    value: str          # natija
    unit: Optional[str] = None        # o'lchov birligi
    reference: Optional[str] = None   # me'yor

class LabResultCreate(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    test_name: str
    test_category: Optional[str] = None
    results: Optional[List[LabResultItem]] = None
    notes: Optional[str] = None

class LabResultUpdate(BaseModel):
    test_name: Optional[str] = None
    test_category: Optional[str] = None
    results: Optional[List[LabResultItem]] = None
    status: Optional[LabResultStatus] = None
    notes: Optional[str] = None

class LabResultResponse(BaseModel):
    id: int
    clinic_id: int
    patient_id: int
    doctor_id: Optional[int]
    entered_by: Optional[int]
    test_name: str
    test_category: Optional[str]
    results: Optional[List[LabResultItem]]
    file_path: Optional[str]
    status: LabResultStatus
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True