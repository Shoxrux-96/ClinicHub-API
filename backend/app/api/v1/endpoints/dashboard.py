from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Any
from datetime import datetime, timedelta, date

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.dashboard import (
    DashboardStats, RevenueStats, AppointmentStats,
    PatientStats, DoctorPerformance
)
from app.services.dashboard_service import DashboardService
from app.models.user import User

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    clinic_id: Optional[int] = Query(None, description="Filter by clinic"),
    date_range: Optional[str] = Query("week", description="today, week, month, year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get main dashboard statistics
    """
    # Calculate date range
    end_date = datetime.now().date()
    if date_range == "today":
        start_date = end_date
    elif date_range == "week":
        start_date = end_date - timedelta(days=7)
    elif date_range == "month":
        start_date = end_date - timedelta(days=30)
    elif date_range == "year":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=7)
    
    stats = DashboardService.get_stats(
        db, clinic_id=clinic_id,
        start_date=start_date, end_date=end_date
    )
    return stats

@router.get("/revenue", response_model=RevenueStats)
def get_revenue_stats(
    clinic_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get revenue statistics
    """
    if not start_date:
        start_date = datetime.now().date() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now().date()
    
    stats = DashboardService.get_revenue_stats(
        db, clinic_id=clinic_id,
        start_date=start_date, end_date=end_date
    )
    return stats

@router.get("/appointments", response_model=AppointmentStats)
def get_appointment_stats(
    clinic_id: Optional[int] = Query(None),
    period: Optional[str] = Query("week", description="day, week, month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get appointment statistics
    """
    stats = DashboardService.get_appointment_stats(db, clinic_id=clinic_id, period=period)
    return stats

@router.get("/patients", response_model=PatientStats)
def get_patient_stats(
    clinic_id: Optional[int] = Query(None),
    period: Optional[str] = Query("month", description="week, month, year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get patient statistics
    """
    stats = DashboardService.get_patient_stats(db, clinic_id=clinic_id, period=period)
    return stats

@router.get("/doctors/performance", response_model=list[DoctorPerformance])
def get_doctors_performance(
    clinic_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get doctors performance metrics
    """
    if not start_date:
        start_date = datetime.now().date() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now().date()
    
    performance = DashboardService.get_doctors_performance(
        db, clinic_id=clinic_id,
        start_date=start_date, end_date=end_date
    )
    return performance

@router.get("/recent-activity")
def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get recent system activity
    """
    activities = DashboardService.get_recent_activity(db, limit=limit)
    return activities