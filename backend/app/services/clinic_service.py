from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import datetime

from app.models.clinic import Clinic
from app.models.user import User
from app.schemas.clinic import (
    ClinicCreate, 
    ClinicUpdate, 
    ClinicResponse, 
    ClinicDetailResponse,
    ClinicStats
)
from app.core.security import get_password_hash


class ClinicService:
    """Klinika xizmatlari"""
    
    @staticmethod
    def get_clinics(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Clinic]:
        """Klinikalar ro'yxatini olish"""
        query = db.query(Clinic)
        
        if search:
            query = query.filter(
                Clinic.name.ilike(f"%{search}%") | 
                Clinic.address.ilike(f"%{search}%")
            )
        
        if is_active is not None:
            query = query.filter(Clinic.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_clinic_by_id(db: Session, clinic_id: int) -> Optional[Clinic]:
        """ID bo'yicha klinika olish"""
        return db.query(Clinic).filter(Clinic.id == clinic_id).first()
    
    @staticmethod
    def create_clinic(db: Session, clinic_data: ClinicCreate) -> Clinic:
        """Yangi klinika yaratish"""
        clinic = Clinic(
            name=clinic_data.name,
            address=clinic_data.address,
            phone=clinic_data.phone,
            email=clinic_data.email,
            website=clinic_data.website,
            description=clinic_data.description,
            clinic_type=clinic_data.clinic_type,
            is_active=True
        )
        db.add(clinic)
        db.commit()
        db.refresh(clinic)
        return clinic
    
    @staticmethod
    def update_clinic(
        db: Session, 
        clinic_id: int, 
        clinic_data: ClinicUpdate
    ) -> Optional[Clinic]:
        """Klinika ma'lumotlarini yangilash"""
        clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
        if not clinic:
            return None
        
        update_data = clinic_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(clinic, field, value)
        
        db.commit()
        db.refresh(clinic)
        return clinic
    
    @staticmethod
    def delete_clinic(db: Session, clinic_id: int) -> bool:
        """Klinikani o'chirish"""
        clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
        if not clinic:
            return False
        
        db.delete(clinic)
        db.commit()
        return True
    
    @staticmethod
    def toggle_clinic_active(db: Session, clinic_id: int) -> Optional[Clinic]:
        """Klinika faolligini o'zgartirish"""
        clinic = db.query(Clinic).filter(Clinic.id == clinic_id).first()
        if not clinic:
            return None
        
        clinic.is_active = not clinic.is_active
        db.commit()
        db.refresh(clinic)
        return clinic
    
    @staticmethod
    def get_clinics_stats(db: Session) -> ClinicStats:
        """Klinikalar statistikasini olish"""
        total_clinics = db.query(Clinic).count()
        active_clinics = db.query(Clinic).filter(Clinic.is_active == True).count()
        
        # Klinika turlari bo'yicha statistika
        from sqlalchemy import func
        clinics_by_type = db.query(
            Clinic.clinic_type, 
            func.count(Clinic.id)
        ).group_by(Clinic.clinic_type).all()
        
        clinics_by_type_dict = {str(k): v for k, v in clinics_by_type}
        
        return ClinicStats(
            total_clinics=total_clinics,
            active_clinics=active_clinics,
            clinics_by_type=clinics_by_type_dict
        )
    
    @staticmethod
    def get_clinic_doctors(db: Session, clinic_id: int) -> List[dict]:
        """Klinika shifokorlarini olish"""
        from app.models.user import User
        
        doctors = db.query(User).filter(
            User.clinic_id == clinic_id,
            User.role == "doctor",
            User.is_active == True
        ).all()
        
        return [
            {
                "id": doctor.id,
                "full_name": doctor.full_name,
                "specialization": doctor.specialization,
                "room_number": doctor.room_number,
                "email": doctor.email,
                "phone": doctor.phone
            }
            for doctor in doctors
        ]
    
    @staticmethod
    def get_clinic_patients(db: Session, clinic_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Klinika bemorlarini olish"""
        from app.models.patient import Patient
        
        patients = db.query(Patient).filter(
            Patient.clinic_id == clinic_id,
            Patient.is_active == True
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": patient.id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "phone": patient.phone,
                "email": patient.email
            }
            for patient in patients
        ]
    
    @staticmethod
    def get_clinic_appointments(
        db: Session, 
        clinic_id: int, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[dict]:
        """Klinika uchrashuvlarini olish"""
        from app.models.appointment import Appointment
        
        query = db.query(Appointment).filter(Appointment.clinic_id == clinic_id)
        
        if date_from:
            query = query.filter(Appointment.appointment_date >= date_from)
        if date_to:
            query = query.filter(Appointment.appointment_date <= date_to)
        
        appointments = query.order_by(Appointment.appointment_date.desc()).all()
        
        return [
            {
                "id": apt.id,
                "patient_id": apt.patient_id,
                "doctor_id": apt.doctor_id,
                "appointment_date": apt.appointment_date,
                "appointment_time": apt.appointment_time,
                "status": apt.status,
                "type": apt.type
            }
            for apt in appointments
        ]
    
    @staticmethod
    def get_clinic_revenue(
        db: Session, 
        clinic_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Klinika daromadini olish"""
        from app.models.payment import Payment
        
        query = db.query(Payment).filter(
            Payment.clinic_id == clinic_id,
            Payment.status == "paid"
        )
        
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        
        payments = query.all()
        total_revenue = sum(p.amount for p in payments)
        
        return {
            "total_revenue": total_revenue,
            "transaction_count": len(payments),
            "average_transaction": total_revenue / len(payments) if payments else 0
        }