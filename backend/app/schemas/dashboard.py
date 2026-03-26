from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date
from enum import Enum


# ==================== DASHBOARD STATS ====================

class DashboardStats(BaseModel):
    """Dashboard statistikasi"""
    total_patients: int = 0
    total_appointments: int = 0
    total_doctors: int = 0
    total_clinics: int = 0
    total_revenue: float = 0.0
    today_appointments: int = 0
    pending_payments: float = 0.0
    new_patients_today: int = 0
    completed_appointments: int = 0
    cancelled_appointments: int = 0


class RevenueStats(BaseModel):
    """Daromad statistikasi"""
    daily_revenue: List[dict] = Field(default_factory=list)
    weekly_revenue: List[dict] = Field(default_factory=list)
    monthly_revenue: List[dict] = Field(default_factory=list)
    yearly_revenue: List[dict] = Field(default_factory=list)
    total_revenue: float = 0.0
    average_daily: float = 0.0
    average_weekly: float = 0.0
    average_monthly: float = 0.0
    growth_percentage: float = 0.0


class AppointmentStats(BaseModel):
    """Uchrashuv statistikasi"""
    total: int = 0
    scheduled: int = 0
    confirmed: int = 0
    completed: int = 0
    cancelled: int = 0
    no_show: int = 0
    today: int = 0
    tomorrow: int = 0
    this_week: int = 0
    completion_rate: float = 0.0
    cancellation_rate: float = 0.0


class PatientStats(BaseModel):
    """Bemor statistikasi"""
    total: int = 0
    active: int = 0
    new_this_month: int = 0
    new_this_week: int = 0
    new_today: int = 0
    returning: int = 0
    by_gender: dict = Field(default_factory=dict)
    by_age_group: dict = Field(default_factory=dict)


class DoctorPerformance(BaseModel):
    """Shifokor faoliyati"""
    doctor_id: int
    doctor_name: str
    specialization: Optional[str] = None
    total_appointments: int = 0
    completed_appointments: int = 0
    cancelled_appointments: int = 0
    no_show_appointments: int = 0
    average_rating: float = 0.0
    total_revenue: float = 0.0
    patients_served: int = 0
    attendance_rate: float = 0.0


class RecentActivity(BaseModel):
    """So'nggi faoliyat"""
    id: int
    activity_type: str
    description: str
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    created_at: datetime
    metadata: Optional[dict] = None


class ChartData(BaseModel):
    """Diagramma ma'lumotlari"""
    labels: List[str] = Field(default_factory=list)
    datasets: List[dict] = Field(default_factory=list)


class MetricCard(BaseModel):
    """Metrik karta"""
    title: str
    value: Any
    change: Optional[float] = None
    change_type: Optional[str] = None  # increase, decrease
    icon: Optional[str] = None
    color: Optional[str] = None


class DashboardFilter(BaseModel):
    """Dashboard filtri"""
    clinic_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    period: Optional[str] = Field("week", description="today, week, month, year")