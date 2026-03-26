from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentStatus


class PaymentService:
    """To'lovlar uchun service"""

    @staticmethod
    def get_payments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        patient_id: Optional[int] = None,
        clinic_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Payment]:
        """To'lovlar ro'yxatini olish"""
        query = db.query(Payment)

        if patient_id:
            query = query.filter(Payment.patient_id == patient_id)
        if clinic_id:
            query = query.filter(Payment.clinic_id == clinic_id)
        if status:
            query = query.filter(Payment.status == status)

        return query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_payment_by_id(db: Session, payment_id: int) -> Optional[Payment]:
        """ID bo'yicha to'lov olish"""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def create_payment(db: Session, payment_data: PaymentCreate) -> Payment:
        """Yangi to'lov yaratish"""
        payment = Payment(
            patient_id=payment_data.patient_id,
            clinic_id=payment_data.clinic_id,
            appointment_id=payment_data.appointment_id,
            amount=payment_data.amount,
            method=payment_data.method,
            type=payment_data.type,
            status=PaymentStatus.PAID,
            description=payment_data.description,
            payment_date=datetime.now()
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def update_status(
        db: Session,
        payment_id: int,
        status: PaymentStatus
    ) -> Optional[Payment]:
        """To'lov holatini yangilash"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            return None

        payment.status = status
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_statistics(
        db: Session,
        clinic_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """To'lovlar statistikasi"""
        query = db.query(Payment)

        if clinic_id:
            query = query.filter(Payment.clinic_id == clinic_id)

        payments = query.all()
        total_amount = sum(p.amount for p in payments if p.status == PaymentStatus.PAID)

        return {
            "total_payments": len(payments),
            "total_amount": total_amount,
            "average_payment": total_amount / len(payments) if payments else 0
        }