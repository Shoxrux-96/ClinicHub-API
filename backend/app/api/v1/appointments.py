from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from app.core.deps import require_reception, get_current_active_user, check_clinic_access
from app.models.user import User
from app.models.appointment import AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/clinics/{clinic_id}/appointments", tags=["Appointments"])

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(
    clinic_id: int,
    appointment_date: Optional[date] = Query(None),
    doctor_id: Optional[int] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    return AppointmentService.get_all(db, clinic_id, appointment_date, doctor_id, status, skip, limit)

@router.get("/today", response_model=List[AppointmentResponse])
def get_today_appointments(
    clinic_id: int,
    doctor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    today = date.today()
    return AppointmentService.get_all(db, clinic_id, today, doctor_id, None, 0, 200)

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    clinic_id: int,
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    return AppointmentService.get_by_id(db, appointment_id, clinic_id)

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    clinic_id: int,
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    return AppointmentService.create(db, clinic_id, current_user.id, data)

# ─── PUT ────────────────────────────────────────────────────────────────────

@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    clinic_id: int,
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    return AppointmentService.update(db, appointment_id, clinic_id, data)

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    clinic_id: int,
    appointment_id: int,
    new_status: AppointmentStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    return AppointmentService.update_status(db, appointment_id, clinic_id, new_status)

@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def partial_update_appointment(
    clinic_id: int,
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    return AppointmentService.update(db, appointment_id, clinic_id, data)

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{appointment_id}", status_code=204)
def cancel_appointment(
    clinic_id: int,
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    AppointmentService.delete(db, appointment_id, clinic_id)