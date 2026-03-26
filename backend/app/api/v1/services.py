from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import require_admin, get_current_active_user, check_clinic_access
from app.models.user import User
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from fastapi import HTTPException

router = APIRouter(prefix="/clinics/{clinic_id}/services", tags=["Services"])

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ServiceResponse])
def get_services(
    clinic_id: int,
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    query = db.query(Service).filter(Service.clinic_id == clinic_id)
    if category:
        query = query.filter(Service.category == category)
    if is_active is not None:
        query = query.filter(Service.is_active == is_active)
    return query.all()

@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    clinic_id: int,
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.clinic_id == clinic_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    return service

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=ServiceResponse, status_code=201)
def create_service(
    clinic_id: int,
    data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    service = Service(clinic_id=clinic_id, **data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

# ─── PUT ────────────────────────────────────────────────────────────────────

@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    clinic_id: int,
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.clinic_id == clinic_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{service_id}", response_model=ServiceResponse)
def partial_update_service(
    clinic_id: int,
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.clinic_id == clinic_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service

@router.patch("/{service_id}/toggle-active", response_model=ServiceResponse)
def toggle_service_active(
    clinic_id: int,
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.clinic_id == clinic_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    service.is_active = not service.is_active
    db.commit()
    db.refresh(service)
    return service

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{service_id}", status_code=204)
def delete_service(
    clinic_id: int,
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.clinic_id == clinic_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    db.delete(service)
    db.commit()