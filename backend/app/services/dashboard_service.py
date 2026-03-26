from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timedelta

from app.models.user import User
from app.models.clinic import Clinic
from app.models.appointment import Appointment
from app.models.payment import Payment
from app.models.patient import Patient
from app.schemas.dashboard import DashboardStats, RevenueStats, AppointmentStats, PatientStats


class DashboardService:
    """Dashboard uchun service"""

    @staticmethod
    def get_stats(
        db: Session,
        clinic_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> DashboardStats:
        """Dashboard statistikasini olish"""
        
        # Klinika filtri
        clinic_filter = []
        if clinic_id:
            clinic_filter.append(Clinic.id == clinic_id)

        # Bemorlar soni
        patients_query = db.query(Patient)
        if clinic_id:
            patients_query = patients_query.filter(Patient.clinic_id == clinic_id)
        total_patients = patients_query.count()

        # Shifokorlar soni
        doctors_query = db.query(User).filter(User.role == "doctor")
        if clinic_id:
            doctors_query = doctors_query.filter(User.clinic_id == clinic_id)
        total_doctors = doctors_query.count()

        # Klinikalar soni
        clinics_query = db.query(Clinic)
        if clinic_id:
            clinics_query = clinics_query.filter(Clinic.id == clinic_id)
        total_clinics = clinics_query.count()

        # Uchrashuvlar soni
        appointments_query = db.query(Appointment)
        if clinic_id:
            appointments_query = appointments_query.filter(Appointment.clinic_id == clinic_id)
        
        today = date.today()
        today_appointments = appointments_query.filter(
            Appointment.appointment_date == today
        ).count()
        
        total_appointments = appointments_query.count()
        
        completed_appointments = appointments_query.filter(
            Appointment.status == "completed"
        ).count()
        
        cancelled_appointments = appointments_query.filter(
            Appointment.status == "cancelled"
        ).count()

        # To'lovlar
        payments_query = db.query(Payment)
        if clinic_id:
            payments_query = payments_query.filter(Payment.clinic_id == clinic_id)
        
        total_revenue = payments_query.filter(
            Payment.status == "paid"
        ).with_entities(db.func.sum(Payment.amount)).scalar() or 0
        
        pending_payments = payments_query.filter(
            Payment.status == "pending"
        ).with_entities(db.func.sum(Payment.amount)).scalar() or 0

        # Yangi bemorlar
        new_patients_today = patients_query.filter(
            Patient.created_at >= datetime.combine(today, datetime.min.time())
        ).count()

        return DashboardStats(
            total_patients=total_patients,
            total_appointments=total_appointments,
            total_doctors=total_doctors,
            total_clinics=total_clinics,
            total_revenue=total_revenue,
            today_appointments=today_appointments,
            pending_payments=pending_payments,
            new_patients_today=new_patients_today,
            completed_appointments=completed_appointments,
            cancelled_appointments=cancelled_appointments
        )

    @staticmethod
    def get_revenue_stats(
        db: Session,
        clinic_id: Optional[int] = None,
        period: str = "week"
    ) -> RevenueStats:
        """Daromad statistikasini olish"""
        
        query = db.query(Payment).filter(Payment.status == "paid")
        if clinic_id:
            query = query.filter(Payment.clinic_id == clinic_id)

        today = date.today()
        
        if period == "today":
            start_date = today
            end_date = today
        elif period == "week":
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == "month":
            start_date = today - timedelta(days=30)
            end_date = today
        elif period == "year":
            start_date = today - timedelta(days=365)
            end_date = today
        else:
            start_date = today - timedelta(days=7)
            end_date = today

        query = query.filter(Payment.payment_date >= start_date, Payment.payment_date <= end_date)
        payments = query.all()
        
        total_revenue = sum(p.amount for p in payments)
        
        # Kunlik daromad
        daily_revenue = []
        for i in range(7):
            day = end_date - timedelta(days=i)
            day_revenue = sum(p.amount for p in payments if p.payment_date.date() == day)
            daily_revenue.append({"date": day.strftime("%Y-%m-%d"), "revenue": day_revenue})

        return RevenueStats(
            total_revenue=total_revenue,
            daily_revenue=daily_revenue,
            weekly_revenue=[],
            monthly_revenue=[],
            yearly_revenue=[],
            average_daily=total_revenue / 7 if daily_revenue else 0,
            average_weekly=total_revenue,
            average_monthly=0,
            growth_percentage=0
        )

    @staticmethod
    def get_appointment_stats(
        db: Session,
        clinic_id: Optional[int] = None,
        period: str = "week"
    ) -> AppointmentStats:
        """Uchrashuv statistikasini olish"""
        
        query = db.query(Appointment)
        if clinic_id:
            query = query.filter(Appointment.clinic_id == clinic_id)

        today = date.today()
        
        total = query.count()
        scheduled = query.filter(Appointment.status == "scheduled").count()
        confirmed = query.filter(Appointment.status == "confirmed").count()
        completed = query.filter(Appointment.status == "completed").count()
        cancelled = query.filter(Appointment.status == "cancelled").count()
        today_count = query.filter(Appointment.appointment_date == today).count()
        tomorrow_count = query.filter(Appointment.appointment_date == today + timedelta(days=1)).count()
        this_week = query.filter(Appointment.appointment_date >= today - timedelta(days=7)).count()

        completion_rate = (completed / total * 100) if total > 0 else 0
        cancellation_rate = (cancelled / total * 100) if total > 0 else 0

        return AppointmentStats(
            total=total,
            scheduled=scheduled,
            confirmed=confirmed,
            completed=completed,
            cancelled=cancelled,
            no_show=0,
            today=today_count,
            tomorrow=tomorrow_count,
            this_week=this_week,
            completion_rate=completion_rate,
            cancellation_rate=cancellation_rate
        )

    @staticmethod
    def get_patient_stats(
        db: Session,
        clinic_id: Optional[int] = None,
        period: str = "month"
    ) -> PatientStats:
        """Bemor statistikasini olish"""
        
        query = db.query(Patient)
        if clinic_id:
            query = query.filter(Patient.clinic_id == clinic_id)

        today = date.today()
        
        total = query.count()
        active = query.filter(Patient.is_active == True).count()
        
        # Yangi bemorlar
        new_this_month = query.filter(
            Patient.created_at >= datetime.combine(today.replace(day=1), datetime.min.time())
        ).count()
        
        new_this_week = query.filter(
            Patient.created_at >= datetime.combine(today - timedelta(days=7), datetime.min.time())
        ).count()
        
        new_today = query.filter(
            Patient.created_at >= datetime.combine(today, datetime.min.time())
        ).count()

        # Jins bo'yicha
        male = query.filter(Patient.gender == "male").count()
        female = query.filter(Patient.gender == "female").count()
        other = query.filter(Patient.gender == "other").count()

        return PatientStats(
            total=total,
            active=active,
            new_this_month=new_this_month,
            new_this_week=new_this_week,
            new_today=new_today,
            returning=total - new_this_month,
            by_gender={"male": male, "female": female, "other": other},
            by_age_group={}
        )

    @staticmethod
    def get_doctors_performance(
        db: Session,
        clinic_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> list:
        """Shifokorlar faoliyatini olish"""
        
        from app.models.user import User
        
        doctors_query = db.query(User).filter(User.role == "doctor")
        if clinic_id:
            doctors_query = doctors_query.filter(User.clinic_id == clinic_id)
        
        doctors = doctors_query.all()
        
        performance = []
        for doctor in doctors:
            appointments = db.query(Appointment).filter(
                Appointment.doctor_id == doctor.id
            )
            
            if start_date:
                appointments = appointments.filter(Appointment.appointment_date >= start_date)
            if end_date:
                appointments = appointments.filter(Appointment.appointment_date <= end_date)
            
            appointments_list = appointments.all()
            total = len(appointments_list)
            completed = len([a for a in appointments_list if a.status == "completed"])
            cancelled = len([a for a in appointments_list if a.status == "cancelled"])
            
            performance.append({
                "doctor_id": doctor.id,
                "doctor_name": doctor.full_name,
                "specialization": doctor.specialization,
                "total_appointments": total,
                "completed_appointments": completed,
                "cancelled_appointments": cancelled,
                "attendance_rate": (completed / total * 100) if total > 0 else 0
            })
        
        return performance

    @staticmethod
    def get_recent_activity(db: Session, limit: int = 10) -> list:
        """So'nggi faoliyatni olish"""
        
        # Uchrashuvlar
        appointments = db.query(Appointment).order_by(
            Appointment.created_at.desc()
        ).limit(limit).all()
        
        activities = []
        for apt in appointments:
            activities.append({
                "id": apt.id,
                "activity_type": "appointment",
                "description": f"New appointment created for patient {apt.patient_id}",
                "created_at": apt.created_at
            })
        
        # To'lovlar
        payments = db.query(Payment).order_by(
            Payment.created_at.desc()
        ).limit(limit).all()
        
        for pay in payments:
            activities.append({
                "id": pay.id,
                "activity_type": "payment",
                "description": f"Payment of {pay.amount} received",
                "created_at": pay.created_at
            })
        
        # Vaqt bo'yicha saralash
        activities.sort(key=lambda x: x["created_at"], reverse=True)
        
        return activities[:limit]