from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, 
    AppointmentResponse, AppointmentStatus
)


class AppointmentService:
    """Uchrashuvlar uchun service"""

    @staticmethod
    def get_appointments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        clinic_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Appointment]:
        """Uchrashuvlar ro'yxatini olish"""
        query = db.query(Appointment)

        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)
        if clinic_id:
            query = query.filter(Appointment.clinic_id == clinic_id)
        if status:
            query = query.filter(Appointment.status == status)
        if start_date:
            query = query.filter(Appointment.appointment_date >= start_date)
        if end_date:
            query = query.filter(Appointment.appointment_date <= end_date)

        return query.order_by(Appointment.appointment_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_appointment_by_id(db: Session, appointment_id: int) -> Optional[Appointment]:
        """ID bo'yicha uchrashuv olish"""
        return db.query(Appointment).filter(Appointment.id == appointment_id).first()

    @staticmethod
    def create_appointment(db: Session, appointment_data: AppointmentCreate) -> Appointment:
        """Yangi uchrashuv yaratish"""
        appointment = Appointment(
            patient_id=appointment_data.patient_id,
            doctor_id=appointment_data.doctor_id,
            clinic_id=appointment_data.clinic_id,
            appointment_date=appointment_data.appointment_date,
            appointment_time=appointment_data.appointment_time,
            duration=appointment_data.duration,
            type=appointment_data.type,
            status=AppointmentStatus.SCHEDULED,
            reason=appointment_data.reason,
            symptoms=appointment_data.symptoms,
            notes=appointment_data.notes
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def update_appointment(
        db: Session,
        appointment_id: int,
        appointment_data: AppointmentUpdate
    ) -> Optional[Appointment]:
        """Uchrashuv ma'lumotlarini yangilash"""
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return None

        update_data = appointment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)

        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def update_status(
        db: Session,
        appointment_id: int,
        status: AppointmentStatus
    ) -> Optional[Appointment]:
        """Uchrashuv holatini yangilash"""
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return None

        appointment.status = status
        if status == AppointmentStatus.COMPLETED:
            appointment.completed_at = datetime.now()
        elif status == AppointmentStatus.CANCELLED:
            appointment.cancelled_at = datetime.now()

        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def cancel_appointment(db: Session, appointment_id: int) -> bool:
        """Uchrashuvni bekor qilish"""
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return False

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.now()
        db.commit()
        return True

    @staticmethod
    def check_availability(
        db: Session,
        doctor_id: int,
        appointment_time: str,
        duration: int,
        appointment_date: Optional[date] = None
    ) -> bool:
        """Shifokorning bandligini tekshirish"""
        if not appointment_date:
            appointment_date = date.today()

        existing = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status != AppointmentStatus.CANCELLED
        ).first()

        return existing is None

    @staticmethod
    def get_doctor_schedule(db: Session, doctor_id: int, date: date) -> List[dict]:
        """Shifokorning kunlik jadvalini olish"""
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == date,
            Appointment.status != AppointmentStatus.CANCELLED
        ).all()

        return [
            {
                "time": apt.appointment_time,
                "patient_name": f"{apt.patient.first_name} {apt.patient.last_name}",
                "status": apt.status,
                "duration": apt.duration
            }
            for apt in appointments
        ]

    @staticmethod
    def get_statistics(
        db: Session,
        clinic_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> dict:
        """Uchrashuvlar statistikasi"""
        query = db.query(Appointment)

        if clinic_id:
            query = query.filter(Appointment.clinic_id == clinic_id)
        if start_date:
            query = query.filter(Appointment.appointment_date >= start_date)
        if end_date:
            query = query.filter(Appointment.appointment_date <= end_date)

        total = query.count()
        scheduled = query.filter(Appointment.status == AppointmentStatus.SCHEDULED).count()
        confirmed = query.filter(Appointment.status == AppointmentStatus.CONFIRMED).count()
        completed = query.filter(Appointment.status == AppointmentStatus.COMPLETED).count()
        cancelled = query.filter(Appointment.status == AppointmentStatus.CANCELLED).count()

        return {
            "total_appointments": total,
            "scheduled": scheduled,
            "confirmed": confirmed,
            "completed": completed,
            "cancelled": cancelled,
            "no_show": 0,
            "today_appointments": 0,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }