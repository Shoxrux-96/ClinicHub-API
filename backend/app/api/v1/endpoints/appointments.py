from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentDetailResponse, AppointmentStatus, AppointmentStatistics
)
from app.services.appointment_service import AppointmentService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[AppointmentResponse])
def get_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    patient_id: Optional[int] = Query(None, description="Filter by patient"),
    clinic_id: Optional[int] = Query(None, description="Filter by clinic"),
    doctor_id: Optional[int] = Query(None, description="Filter by doctor"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all appointments with filters
    """
    # Foydalanuvchi o'z klinikasining uchrashuvlarini ko'ra oladi
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            appointments = AppointmentService.get_appointments(
                db, skip=skip, limit=limit,
                patient_id=patient_id, clinic_id=current_user.clinic_id,
                doctor_id=doctor_id, status=status,
                start_date=start_date, end_date=end_date
            )
            return appointments
        return []
    
    appointments = AppointmentService.get_appointments(
        db, skip=skip, limit=limit,
        patient_id=patient_id, clinic_id=clinic_id,
        doctor_id=doctor_id, status=status,
        start_date=start_date, end_date=end_date
    )
    return appointments


@router.get("/statistics", response_model=AppointmentStatistics)
def get_appointment_statistics(
    clinic_id: Optional[int] = Query(None, description="Filter by clinic"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get appointment statistics
    """
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            clinic_id = current_user.clinic_id
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return AppointmentService.get_statistics(
        db, clinic_id=clinic_id,
        start_date=start_date, end_date=end_date
    )


@router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get appointment by ID
    """
    appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != appointment.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return appointment


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new appointment
    """
    # Klinika ID sini o'rnatish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            appointment_data.clinic_id = current_user.clinic_id
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have a clinic assigned"
            )
    
    # Check availability
    if not AppointmentService.check_availability(
        db, appointment_data.doctor_id,
        appointment_data.appointment_time,
        appointment_data.duration,
        appointment_data.appointment_date
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor is not available at this time"
        )
    
    appointment = AppointmentService.create_appointment(db, appointment_data)
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update appointment
    """
    appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != appointment.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    updated_appointment = AppointmentService.update_appointment(db, appointment_id, appointment_data)
    return updated_appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status: AppointmentStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update appointment status
    """
    appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != appointment.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    updated_appointment = AppointmentService.update_status(db, appointment_id, status)
    return updated_appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Cancel appointment
    """
    appointment = AppointmentService.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != appointment.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    success = AppointmentService.cancel_appointment(db, appointment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    # 204 status code da hech narsa qaytarmaymiz
    return None


@router.get("/doctor/{doctor_id}/schedule", response_model=List[dict])
def get_doctor_schedule(
    doctor_id: int,
    date: date = Query(..., description="Date to check schedule"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get doctor's schedule for specific date
    """
    schedule = AppointmentService.get_doctor_schedule(db, doctor_id, date)
    return schedule


@router.get("/my-appointments", response_model=List[AppointmentResponse])
def get_my_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AppointmentStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user's appointments
    """
    appointments = AppointmentService.get_appointments(
        db, skip=skip, limit=limit,
        patient_id=current_user.id if current_user.role == "patient" else None,
        doctor_id=current_user.id if current_user.role == "doctor" else None,
        status=status
    )
    return appointments


@router.get("/today", response_model=List[AppointmentResponse])
def get_today_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get today's appointments
    """
    today = date.today()
    
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            appointments = AppointmentService.get_appointments(
                db, clinic_id=current_user.clinic_id,
                start_date=today, end_date=today
            )
            return appointments
        return []
    
    appointments = AppointmentService.get_appointments(
        db, start_date=today, end_date=today
    )
    return appointments