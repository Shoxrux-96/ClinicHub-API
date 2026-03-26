from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import require_admin, require_owner, get_current_active_user, check_clinic_access
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserChangePassword
from app.services.user_service import UserService

router = APIRouter(prefix="/clinics/{clinic_id}/users", tags=["Users"])

# ─── GET ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[UserResponse])
def get_users(
    clinic_id: int,
    role: Optional[UserRole] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    return UserService.get_all(db, clinic_id, role)

@router.get("/doctors", response_model=List[UserResponse])
def get_doctors(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    return UserService.get_all(db, clinic_id, role=UserRole.DOCTOR)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    clinic_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    return UserService.get_by_id(db, user_id, clinic_id)

# ─── POST ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    clinic_id: int,
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    # Admin faqat doctor va reception yarata oladi
    if current_user.role == UserRole.ADMIN and data.role not in [UserRole.DOCTOR, UserRole.RECEPTION]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin faqat doctor va reception yarata oladi")
    return UserService.create(db, clinic_id, data)

# ─── PUT ────────────────────────────────────────────────────────────────────

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    clinic_id: int,
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    return UserService.update(db, user_id, clinic_id, data)

# ─── PATCH ──────────────────────────────────────────────────────────────────

@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(
    clinic_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    user = UserService.get_by_id(db, user_id, clinic_id)
    return UserService.update(db, user_id, clinic_id, UserUpdate(is_active=not user.is_active))

@router.patch("/me/change-password")
def change_password(
    clinic_id: int,
    data: UserChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return UserService.change_password(db, current_user.id, data)

# ─── DELETE ─────────────────────────────────────────────────────────────────

@router.delete("/{user_id}", status_code=204)
def delete_user(
    clinic_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    UserService.delete(db, user_id, clinic_id)