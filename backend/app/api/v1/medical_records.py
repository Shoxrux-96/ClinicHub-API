from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import require_doctor, get_current_active_user, check_clinic_access
from app.models.user import User, UserRole
from app.models.medical_record import MedicalRecord
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse
from fastapi import HTTPException

router = APIRouter(prefix="/clinics/{clinic_id}/medical-records", tags=["Medical Records"])

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[MedicalRecordResponse])
def get_medical_records(
    clinic_id: int,
    patient_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    query = db.query(MedicalRecord).filter(MedicalRecord.clinic_id == clinic_id)
    if patient_id:
        query = query.filter(MedicalRecord.patient_id == patient_id)
    # Doctor faqat o'zinikini ko'radi agar filter yo'q bo'lsa
    if current_user.role == UserRole.DOCTOR and not patient_id:
        query = query.filter(MedicalRecord.doctor_id == current_user.id)
    return query.order_by(MedicalRecord.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{record_id}", response_model=MedicalRecordResponse)
def get_medical_record(
    clinic_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id,
        MedicalRecord.clinic_id == clinic_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Yozuv topilmadi")
    return record

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=MedicalRecordResponse, status_code=201)
def create_medical_record(
    clinic_id: int,
    data: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    check_clinic_access(clinic_id, current_user)
    prescription_data = None
    if data.prescription:
        prescription_data = [p.model_dump() for p in data.prescription]

    record = MedicalRecord(
        clinic_id=clinic_id,
        doctor_id=current_user.id,
        patient_id=data.patient_id,
        appointment_id=data.appointment_id,
        complaint=data.complaint,
        anamnesis=data.anamnesis,
        examination=data.examination,
        diagnosis=data.diagnosis,
        diagnosis_code=data.diagnosis_code,
        treatment=data.treatment,
        prescription=prescription_data,
        recommendations=data.recommendations,
        next_visit_date=data.next_visit_date
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

# ─── PUT ────────────────────────────────────────────────────────────────────

@router.put("/{record_id}", response_model=MedicalRecordResponse)
def update_medical_record(
    clinic_id: int,
    record_id: int,
    data: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    check_clinic_access(clinic_id, current_user)
    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id,
        MedicalRecord.clinic_id == clinic_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Yozuv topilmadi")
    if current_user.role == UserRole.DOCTOR and record.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Faqat o'z yozuvingizni tahrirlash mumkin")

    update_data = data.model_dump(exclude_none=True)
    if "prescription" in update_data and update_data["prescription"]:
        update_data["prescription"] = [p.model_dump() for p in data.prescription]
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{record_id}", response_model=MedicalRecordResponse)
def partial_update_medical_record(
    clinic_id: int,
    record_id: int,
    data: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    check_clinic_access(clinic_id, current_user)
    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id,
        MedicalRecord.clinic_id == clinic_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Yozuv topilmadi")
    update_data = data.model_dump(exclude_none=True)
    if "prescription" in update_data and update_data["prescription"]:
        update_data["prescription"] = [p.model_dump() for p in data.prescription]
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{record_id}", status_code=204)
def delete_medical_record(
    clinic_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    check_clinic_access(clinic_id, current_user)
    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id,
        MedicalRecord.clinic_id == clinic_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Yozuv topilmadi")
    db.delete(record)
    db.commit()