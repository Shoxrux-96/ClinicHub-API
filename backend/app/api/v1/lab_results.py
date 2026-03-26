from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import require_reception, get_current_active_user, check_clinic_access
from app.models.user import User
from app.models.lab_result import LabResult, LabResultStatus
from app.schemas.lab_result import LabResultCreate, LabResultUpdate, LabResultResponse
from fastapi import HTTPException
import shutil, os

router = APIRouter(prefix="/clinics/{clinic_id}/lab-results", tags=["Lab Results"])

UPLOAD_DIR = "uploads/lab_results"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[LabResultResponse])
def get_lab_results(
    clinic_id: int,
    patient_id: Optional[int] = Query(None),
    status: Optional[LabResultStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    query = db.query(LabResult).filter(LabResult.clinic_id == clinic_id)
    if patient_id:
        query = query.filter(LabResult.patient_id == patient_id)
    if status:
        query = query.filter(LabResult.status == status)
    return query.order_by(LabResult.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{result_id}", response_model=LabResultResponse)
def get_lab_result(
    clinic_id: int,
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    result = db.query(LabResult).filter(
        LabResult.id == result_id,
        LabResult.clinic_id == clinic_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Tahlil natijasi topilmadi")
    return result

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=LabResultResponse, status_code=201)
def create_lab_result(
    clinic_id: int,
    data: LabResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    results_data = None
    if data.results:
        results_data = [r.model_dump() for r in data.results]

    lab_result = LabResult(
        clinic_id=clinic_id,
        entered_by=current_user.id,
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        test_name=data.test_name,
        test_category=data.test_category,
        results=results_data,
        notes=data.notes
    )
    db.add(lab_result)
    db.commit()
    db.refresh(lab_result)
    return lab_result

@router.post("/{result_id}/upload-file", response_model=LabResultResponse)
def upload_lab_result_file(
    clinic_id: int,
    result_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    result = db.query(LabResult).filter(
        LabResult.id == result_id,
        LabResult.clinic_id == clinic_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Tahlil natijasi topilmadi")

    file_path = f"{UPLOAD_DIR}/{clinic_id}_{result_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result.file_path = file_path
    result.status = LabResultStatus.READY
    db.commit()
    db.refresh(result)
    return result

# ─── PUT ────────────────────────────────────────────────────────────────────

@router.put("/{result_id}", response_model=LabResultResponse)
def update_lab_result(
    clinic_id: int,
    result_id: int,
    data: LabResultUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    result = db.query(LabResult).filter(
        LabResult.id == result_id,
        LabResult.clinic_id == clinic_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Topilmadi")
    update_data = data.model_dump(exclude_none=True)
    if "results" in update_data and update_data["results"]:
        update_data["results"] = [r.model_dump() for r in data.results]
    for field, value in update_data.items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    return result

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{result_id}/status", response_model=LabResultResponse)
def update_lab_result_status(
    clinic_id: int,
    result_id: int,
    new_status: LabResultStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    result = db.query(LabResult).filter(
        LabResult.id == result_id,
        LabResult.clinic_id == clinic_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Topilmadi")
    result.status = new_status
    db.commit()
    db.refresh(result)
    return result

@router.patch("/{result_id}", response_model=LabResultResponse)
def partial_update_lab_result(
    clinic_id: int,
    result_id: int,
    data: LabResultUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    result = db.query(LabResult).filter(
        LabResult.id == result_id,
        LabResult.clinic_id == clinic_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Topilmadi")
    update_data = data.model_dump(exclude_none=True)
    if "results" in update_data and update_data["results"]:
        update_data["results"] = [r.model_dump() for r in data.results]
    for field, value in update_data.items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    return result

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{result_id}", status_code=204)
def delete_lab_result(
    clinic_id: int,
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    result = db.query(LabResult).filter(
        LabResult.id == result_id,
        LabResult.clinic_id == clinic_id
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Topilmadi")
    db.delete(result)
    db.commit()