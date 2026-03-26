from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import require_reception, get_current_active_user, check_clinic_access
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services.patient_service import PatientService

router = APIRouter(prefix="/clinics/{clinic_id}/patients", tags=["Patients"])

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[PatientResponse])
def get_patients(
    clinic_id: int,
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    return PatientService.get_all(db, clinic_id, search, skip, limit)

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    clinic_id: int,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    return PatientService.get_by_id(db, patient_id, clinic_id)

@router.get("/{patient_id}/full-history")
def get_patient_full_history(
    clinic_id: int,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    patient = PatientService.get_by_id(db, patient_id, clinic_id)

    from app.models.appointment import Appointment
    from app.models.medical_record import MedicalRecord
    from app.models.lab_result import LabResult
    from app.models.payment import Payment
    from app.schemas.appointment import AppointmentResponse
    from app.schemas.medical_record import MedicalRecordResponse
    from app.schemas.lab_result import LabResultResponse
    from app.schemas.payment import PaymentResponse

    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.clinic_id == clinic_id
    ).order_by(Appointment.appointment_date.desc()).all()

    medical_records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient_id,
        MedicalRecord.clinic_id == clinic_id
    ).order_by(MedicalRecord.created_at.desc()).all()

    lab_results = db.query(LabResult).filter(
        LabResult.patient_id == patient_id,
        LabResult.clinic_id == clinic_id
    ).order_by(LabResult.created_at.desc()).all()

    payments = db.query(Payment).filter(
        Payment.patient_id == patient_id,
        Payment.clinic_id == clinic_id
    ).order_by(Payment.created_at.desc()).all()

    return {
        "patient": PatientResponse.model_validate(patient),
        "appointments": [AppointmentResponse.model_validate(a) for a in appointments],
        "medical_records": [MedicalRecordResponse.model_validate(r) for r in medical_records],
        "lab_results": [LabResultResponse.model_validate(l) for l in lab_results],
        "payments": [PaymentResponse.model_validate(p) for p in payments]
    }

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=PatientResponse, status_code=201)
def create_patient(
    clinic_id: int,
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    return PatientService.create(db, clinic_id, data)

# ─── PUT ────────────────────────────────────────────────────────────────────

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    clinic_id: int,
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    return PatientService.update(db, patient_id, clinic_id, data)

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{patient_id}", response_model=PatientResponse)
def partial_update_patient(
    clinic_id: int,
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    return PatientService.update(db, patient_id, clinic_id, data)

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{patient_id}", status_code=204)
def delete_patient(
    clinic_id: int,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    PatientService.delete(db, patient_id, clinic_id)