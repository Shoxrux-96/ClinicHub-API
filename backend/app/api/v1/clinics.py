from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import require_owner
from app.models.user import User
from app.schemas.clinic import (
    ClinicCreate, ClinicUpdate, ClinicResponse,
    ClinicStats, ClinicSubscriptionUpdate
)
from app.services.clinic_service import ClinicService
from pydantic import BaseModel

router = APIRouter(prefix="/clinics", tags=["Clinics"])

class ClinicCreateWithAdmin(BaseModel):
    clinic: ClinicCreate
    admin_full_name: str
    admin_email: str
    admin_password: str
    admin_phone: Optional[str] = None

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ClinicResponse])
def get_all_clinics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    return ClinicService.get_all(db, skip, limit, is_active)

@router.get("/{clinic_id}", response_model=ClinicResponse)
def get_clinic(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    return ClinicService.get_by_id(db, clinic_id)

@router.get("/{clinic_id}/stats", response_model=ClinicStats)
def get_clinic_stats(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    return ClinicService.get_stats(db, clinic_id)

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=ClinicResponse, status_code=201)
def create_clinic(
    data: ClinicCreateWithAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    admin_data = {
        "full_name": data.admin_full_name,
        "email": data.admin_email,
        "password": data.admin_password,
        "phone": data.admin_phone
    }
    return ClinicService.create(db, data.clinic, admin_data)

# ─── PUT ────────────────────────────────────────────────────────────────────

@router.put("/{clinic_id}", response_model=ClinicResponse)
def update_clinic(
    clinic_id: int,
    data: ClinicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    return ClinicService.update(db, clinic_id, data)

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{clinic_id}/subscription", response_model=ClinicResponse)
def update_subscription(
    clinic_id: int,
    data: ClinicSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    return ClinicService.update_subscription(db, clinic_id, data)

@router.patch("/{clinic_id}/toggle-active", response_model=ClinicResponse)
def toggle_clinic_active(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    clinic = ClinicService.get_by_id(db, clinic_id)
    from app.schemas.clinic import ClinicUpdate
    return ClinicService.update(db, clinic_id, ClinicUpdate(is_active=not clinic.is_active))

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{clinic_id}", status_code=204)
def delete_clinic(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):
    ClinicService.delete(db, clinic_id)