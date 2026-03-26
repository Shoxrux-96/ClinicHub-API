from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.core.database import get_db
from app.core.security import get_current_user, get_current_superuser
from app.schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse,
    PatientDetailResponse, PatientMedicalHistory
)
from app.services.patient_service import PatientService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[PatientResponse])
def get_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, phone or email"),
    clinic_id: Optional[int] = Query(None, description="Filter by clinic"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all patients with pagination and filters
    """
    # Foydalanuvchi o'z klinikasining bemorlarini ko'ra oladi
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            patients = PatientService.get_patients(
                db, skip=skip, limit=limit, 
                search=search, clinic_id=current_user.clinic_id
            )
            return patients
        return []
    
    patients = PatientService.get_patients(
        db, skip=skip, limit=limit, 
        search=search, clinic_id=clinic_id
    )
    return patients


@router.get("/{patient_id}", response_model=PatientDetailResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get patient by ID with detailed information
    """
    patient = PatientService.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != patient.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return patient


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new patient
    """
    # Klinika ID sini o'rnatish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            patient_data.clinic_id = current_user.clinic_id
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have a clinic assigned"
            )
    
    patient = PatientService.create_patient(db, patient_data)
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update patient information
    """
    patient = PatientService.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != patient.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    updated_patient = PatientService.update_patient(db, patient_id, patient_data)
    return updated_patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete patient (Admin only)
    """
    # Faqat superuser o'chira oladi
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete patients"
        )
    
    patient = PatientService.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    success = PatientService.delete_patient(db, patient_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # 204 status code da hech narsa qaytarmaymiz
    return None


@router.get("/{patient_id}/medical-history", response_model=PatientMedicalHistory)
def get_patient_medical_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get patient's medical history
    """
    patient = PatientService.get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != patient.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    history = PatientService.get_medical_history(db, patient_id)
    return history


@router.get("/clinic/{clinic_id}/patients")
def get_clinic_patients(
    clinic_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get patients by clinic ID
    """
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    patients = PatientService.get_patients(
        db, skip=skip, limit=limit, clinic_id=clinic_id
    )
    return {
        "clinic_id": clinic_id,
        "patients": patients,
        "total": len(patients),
        "skip": skip,
        "limit": limit
    }


@router.get("/stats/summary")
def get_patient_statistics(
    clinic_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get patient statistics (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    stats = PatientService.get_patient_statistics(db, clinic_id)
    return stats