from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientStats


class PatientService:
    """Bemorlar uchun service"""

    @staticmethod
    def get_patients(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        clinic_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Patient]:
        """Bemorlar ro'yxatini olish"""
        query = db.query(Patient)

        if clinic_id:
            query = query.filter(Patient.clinic_id == clinic_id)
        if search:
            query = query.filter(
                Patient.first_name.ilike(f"%{search}%") |
                Patient.last_name.ilike(f"%{search}%") |
                Patient.phone.ilike(f"%{search}%")
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_patient_by_id(db: Session, patient_id: int) -> Optional[Patient]:
        """ID bo'yicha bemor olish"""
        return db.query(Patient).filter(Patient.id == patient_id).first()

    @staticmethod
    def create_patient(db: Session, patient_data: PatientCreate) -> Patient:
        """Yangi bemor yaratish"""
        patient = Patient(
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            email=patient_data.email,
            phone=patient_data.phone,
            date_of_birth=patient_data.date_of_birth,
            gender=patient_data.gender,
            blood_type=patient_data.blood_type,
            address=patient_data.address,
            clinic_id=patient_data.clinic_id,
            is_active=True
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def update_patient(
        db: Session,
        patient_id: int,
        patient_data: PatientUpdate
    ) -> Optional[Patient]:
        """Bemor ma'lumotlarini yangilash"""
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None

        update_data = patient_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)

        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def delete_patient(db: Session, patient_id: int) -> bool:
        """Bemorni o'chirish"""
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return False

        db.delete(patient)
        db.commit()
        return True

    @staticmethod
    def get_medical_history(db: Session, patient_id: int) -> Optional[dict]:
        """Bemorning tibbiy tarixini olish"""
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None

        return {
            "patient_id": patient.id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "allergies": [],
            "chronic_conditions": [],
            "current_medications": [],
            "medical_records": []
        }