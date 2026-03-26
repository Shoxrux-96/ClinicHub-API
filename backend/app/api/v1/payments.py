from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from app.core.deps import require_reception, require_admin, get_current_active_user, check_clinic_access
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/clinics/{clinic_id}/payments", tags=["Payments"])

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    clinic_id: int,
    patient_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    return PaymentService.get_all(db, clinic_id, patient_id, skip, limit)

@router.get("/daily-report")
def get_daily_report(
    clinic_id: int,
    report_date: date = Query(default=date.today()),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    return PaymentService.get_daily_report(db, clinic_id, report_date)

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    clinic_id: int,
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    return PaymentService.get_by_id(db, payment_id, clinic_id)

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(
    clinic_id: int,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reception)
):
    check_clinic_access(clinic_id, current_user)
    return PaymentService.create(db, clinic_id, current_user.id, data)

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{payment_id}/notes")
def update_payment_notes(
    clinic_id: int,
    payment_id: int,
    notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    payment = PaymentService.get_by_id(db, payment_id, clinic_id)
    payment.notes = notes
    db.commit()
    return {"message": "Izoh yangilandi"}

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    clinic_id: int,
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    PaymentService.delete(db, payment_id, clinic_id)