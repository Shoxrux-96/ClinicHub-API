from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.core.database import get_db
from app.core.security import get_current_user, get_current_owner
from app.schemas.clinic import (
    ClinicCreate, ClinicUpdate, ClinicResponse, 
    ClinicDetailResponse, ClinicStats
)
from app.services.clinic_service import ClinicService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[ClinicResponse])
def get_clinics(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    search: Optional[str] = Query(None, description="Search by name or address"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all clinics with pagination and filters
    """
    # Owner va superuser barcha klinikalarni ko'ra oladi
    # Boshqa foydalanuvchilar faqat o'z klinikalarini ko'ra oladi
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            clinics = ClinicService.get_clinics(
                db, skip=skip, limit=limit, 
                search=search, is_active=is_active
            )
            # Foydalanuvchining klinikasini filtrlash
            clinics = [c for c in clinics if c.id == current_user.clinic_id]
            return clinics
        return []
    
    clinics = ClinicService.get_clinics(
        db, skip=skip, limit=limit, 
        search=search, is_active=is_active
    )
    return clinics


@router.get("/stats", response_model=ClinicStats)
def get_clinics_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get clinics statistics (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return ClinicService.get_clinics_stats(db)


@router.get("/{clinic_id}", response_model=ClinicDetailResponse)
def get_clinic(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get clinic by ID with detailed information
    """
    # Foydalanuvchi o'z klinikasini yoki admin/owner barchasini ko'ra oladi
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    clinic = ClinicService.get_clinic_by_id(db, clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )
    return clinic


@router.post("/", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
def create_clinic(
    clinic_data: ClinicCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new clinic (Admin/Owner only)
    """
    # Faqat owner yoki superuser yaratishi mumkin
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can create clinics"
        )
    
    clinic = ClinicService.create_clinic(db, clinic_data)
    return clinic


@router.put("/{clinic_id}", response_model=ClinicResponse)
def update_clinic(
    clinic_id: int,
    clinic_data: ClinicUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update clinic information (Admin/Owner only)
    """
    # Faqat owner yoki superuser yangilashi mumkin
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can update clinics"
        )
    
    clinic = ClinicService.update_clinic(db, clinic_id, clinic_data)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )
    return clinic


@router.delete("/{clinic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clinic(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete clinic (Admin/Owner only)
    """
    # Faqat owner yoki superuser o'chira oladi
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete clinics"
        )
    
    success = ClinicService.delete_clinic(db, clinic_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )
    
    # 204 status code da hech narsa qaytarmaymiz
    return None


@router.patch("/{clinic_id}/toggle-active", response_model=ClinicResponse)
def toggle_clinic_active(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Toggle clinic active status (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can modify clinic status"
        )
    
    clinic = ClinicService.toggle_clinic_active(db, clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )
    return clinic


@router.get("/{clinic_id}/doctors")
def get_clinic_doctors(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get clinic doctors
    """
    # Foydalanuvchi o'z klinikasini yoki admin/owner barchasini ko'ra oladi
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    clinic = ClinicService.get_clinic_by_id(db, clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )
    
    doctors = ClinicService.get_clinic_doctors(db, clinic_id)
    return {
        "clinic_id": clinic_id,
        "clinic_name": clinic.name,
        "doctors": doctors,
        "total": len(doctors)
    }


@router.get("/{clinic_id}/patients")
def get_clinic_patients(
    clinic_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get clinic patients
    """
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    clinic = ClinicService.get_clinic_by_id(db, clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found"
        )
    
    patients = ClinicService.get_clinic_patients(db, clinic_id, skip, limit)
    return {
        "clinic_id": clinic_id,
        "clinic_name": clinic.name,
        "patients": patients,
        "total": len(patients),
        "skip": skip,
        "limit": limit
    }


@router.get("/{clinic_id}/revenue")
def get_clinic_revenue(
    clinic_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get clinic revenue (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    revenue = ClinicService.get_clinic_revenue(db, clinic_id, start, end)
    return revenue