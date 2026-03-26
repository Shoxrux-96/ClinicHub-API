from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import date, datetime
from app.core.database import get_db
from app.core.deps import require_admin, get_current_active_user, check_clinic_access
from app.models.user import User
from app.models.payment import Payment
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.medical_record import MedicalRecord
from app.models.lab_result import LabResult
from app.utils.pdf_generator import (
    generate_prescription_pdf,
    generate_patient_card_pdf,
    generate_receipt_pdf,
    generate_monthly_report_pdf
)
from app.utils.excel_generator import (
    generate_monthly_report_excel,
    generate_patients_excel,
    generate_appointments_excel
)
from app.services.patient_service import PatientService
from app.services.clinic_service import ClinicService

router = APIRouter(prefix="/clinics/{clinic_id}/reports", tags=["Reports & PDF"])


# ─── RETSEPT PDF ────────────────────────────────────────────────────────────
@router.get("/prescription/{record_id}/pdf")
def download_prescription_pdf(
    clinic_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)

    from app.models.medical_record import MedicalRecord
    from fastapi import HTTPException

    record = db.query(MedicalRecord).filter(
        MedicalRecord.id == record_id,
        MedicalRecord.clinic_id == clinic_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Yozuv topilmadi")

    clinic = ClinicService.get_by_id(db, clinic_id)
    patient = PatientService.get_by_id(db, record.patient_id, clinic_id)
    doctor = db.query(User).filter(User.id == record.doctor_id).first()

    buffer = generate_prescription_pdf(
        clinic_name=clinic.name,
        clinic_address=clinic.address or "",
        clinic_phone=clinic.phone or "",
        doctor_name=doctor.full_name if doctor else "—",
        doctor_specialization=doctor.specialization or "" if doctor else "",
        patient_name=patient.full_name,
        patient_birth_date=str(patient.birth_date) if patient.birth_date else "",
        diagnosis=record.diagnosis or "",
        prescription=record.prescription or [],
        recommendations=record.recommendations or "",
        next_visit=record.next_visit_date or "",
        record_date=record.created_at.strftime("%d.%m.%Y") if record.created_at else ""
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=retsept_{record_id}.pdf"}
    )


# ─── BEMOR KARTASI PDF ──────────────────────────────────────────────────────
@router.get("/patient-card/{patient_id}/pdf")
def download_patient_card_pdf(
    clinic_id: int,
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)

    clinic = ClinicService.get_by_id(db, clinic_id)
    patient = PatientService.get_by_id(db, patient_id, clinic_id)

    # Barcha ma'lumotlar
    appointments = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.clinic_id == clinic_id
    ).order_by(Appointment.appointment_date.desc()).all()

    medical_records = db.query(MedicalRecord).filter(
        MedicalRecord.patient_id == patient_id,
        MedicalRecord.clinic_id == clinic_id
    ).order_by(MedicalRecord.created_at.desc()).all()

    lab_results = db.query(LabResult).filter(
        LabResult.patient_id == patient_id,
        LabResult.clinic_id == clinic_id
    ).order_by(LabResult.created_at.desc()).all()

    # Doctor nomlarini olish
    doctor_ids = {a.doctor_id for a in appointments} | {r.doctor_id for r in medical_records}
    doctors = {u.id: u for u in db.query(User).filter(User.id.in_(doctor_ids)).all()}

    appt_list = [{
        "appointment_date": str(a.appointment_date),
        "doctor_name": doctors.get(a.doctor_id, type("", (), {"full_name": "—"})()).full_name,
        "queue_number": a.queue_number,
        "status": a.status.value
    } for a in appointments]

    rec_list = [{
        "created_at": a.created_at.strftime("%d.%m.%Y") if a.created_at else "",
        "doctor_name": doctors.get(a.doctor_id, type("", (), {"full_name": "—"})()).full_name,
        "complaint": a.complaint,
        "diagnosis": a.diagnosis,
        "treatment": a.treatment,
        "recommendations": a.recommendations
    } for a in medical_records]

    lab_list = [{
        "test_name": l.test_name,
        "test_category": l.test_category,
        "status": l.status.value,
        "created_at": l.created_at.strftime("%d.%m.%Y") if l.created_at else ""
    } for l in lab_results]

    buffer = generate_patient_card_pdf(
        clinic_name=clinic.name,
        clinic_address=clinic.address or "",
        clinic_phone=clinic.phone or "",
        patient={
            "patient_code": patient.patient_code,
            "full_name": patient.full_name,
            "birth_date": str(patient.birth_date) if patient.birth_date else "",
            "gender": patient.gender.value if patient.gender else "",
            "phone": patient.phone,
            "address": patient.address,
            "blood_type": patient.blood_type.value if patient.blood_type else "",
            "allergies": patient.allergies,
            "chronic_diseases": patient.chronic_diseases
        },
        appointments=appt_list,
        medical_records=rec_list,
        lab_results=lab_list
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=bemor_karta_{patient_id}.pdf"}
    )


# ─── KASSA CHEKI PDF ────────────────────────────────────────────────────────
@router.get("/receipt/{payment_id}/pdf")
def download_receipt_pdf(
    clinic_id: int,
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_clinic_access(clinic_id, current_user)
    from fastapi import HTTPException

    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.clinic_id == clinic_id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi")

    clinic = ClinicService.get_by_id(db, clinic_id)
    patient = PatientService.get_by_id(db, payment.patient_id, clinic_id)
    cashier = db.query(User).filter(User.id == payment.cashier_id).first()

    buffer = generate_receipt_pdf(
        clinic_name=clinic.name,
        clinic_address=clinic.address or "",
        clinic_phone=clinic.phone or "",
        receipt_number=payment.receipt_number,
        patient_name=patient.full_name,
        cashier_name=cashier.full_name if cashier else "—",
        services=payment.services_snapshot or [],
        subtotal=float(payment.subtotal),
        discount=float(payment.discount),
        total_amount=float(payment.total_amount),
        paid_amount=float(payment.paid_amount),
        change_amount=float(payment.change_amount),
        payment_method=payment.payment_method.value,
        payment_date=payment.created_at.strftime("%d.%m.%Y %H:%M") if payment.created_at else ""
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=chek_{payment.receipt_number}.pdf"}
    )


# ─── OYLIK HISOBOT PDF ──────────────────────────────────────────────────────
@router.get("/monthly/pdf")
def download_monthly_report_pdf(
    clinic_id: int,
    year: int = Query(default=datetime.now().year),
    month: int = Query(default=datetime.now().month),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    clinic = ClinicService.get_by_id(db, clinic_id)

    payments = db.query(Payment).filter(
        Payment.clinic_id == clinic_id,
        extract("year", Payment.created_at) == year,
        extract("month", Payment.created_at) == month
    ).all()

    total_patients = db.query(func.count(Patient.id)).filter(
        Patient.clinic_id == clinic_id,
        Patient.is_deleted == False
    ).scalar()

    total_appointments = db.query(func.count(Appointment.id)).filter(
        Appointment.clinic_id == clinic_id,
        extract("year", Appointment.appointment_date) == year,
        extract("month", Appointment.appointment_date) == month
    ).scalar()

    total_revenue = sum(float(p.total_amount) for p in payments)

    revenue_by_method = {}
    for p in payments:
        m = p.payment_method.value
        revenue_by_method[m] = revenue_by_method.get(m, 0) + float(p.total_amount)

    # Kunlik daromad
    daily = {}
    for p in payments:
        day = p.created_at.strftime("%d.%m.%Y") if p.created_at else "—"
        if day not in daily:
            daily[day] = {"date": day, "count": 0, "total": 0}
        daily[day]["count"] += 1
        daily[day]["total"] += float(p.total_amount)
    daily_revenue = sorted(daily.values(), key=lambda x: x["date"])

    # Top xizmatlar
    service_counts: dict = {}
    for p in payments:
        for srv in (p.services_snapshot or []):
            name = srv.get("service_name", "")
            if name not in service_counts:
                service_counts[name] = {"name": name, "count": 0, "revenue": 0}
            service_counts[name]["count"] += int(srv.get("qty", 1))
            service_counts[name]["revenue"] += float(srv.get("price", 0)) * int(srv.get("qty", 1))
    top_services = sorted(service_counts.values(), key=lambda x: x["count"], reverse=True)[:10]

    report_month = f"{month:02d}/{year}"
    buffer = generate_monthly_report_pdf(
        clinic_name=clinic.name,
        report_month=report_month,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_revenue=total_revenue,
        revenue_by_method=revenue_by_method,
        top_services=top_services,
        daily_revenue=daily_revenue
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=hisobot_{report_month.replace('/', '_')}.pdf"}
    )


# ─── OYLIK HISOBOT EXCEL ────────────────────────────────────────────────────
@router.get("/monthly/excel")
def download_monthly_report_excel(
    clinic_id: int,
    year: int = Query(default=datetime.now().year),
    month: int = Query(default=datetime.now().month),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    clinic = ClinicService.get_by_id(db, clinic_id)

    payments = db.query(Payment).filter(
        Payment.clinic_id == clinic_id,
        extract("year", Payment.created_at) == year,
        extract("month", Payment.created_at) == month
    ).all()

    patient_ids = {p.patient_id for p in payments}
    cashier_ids = {p.cashier_id for p in payments}
    patients_map = {u.id: u for u in db.query(Patient).filter(Patient.id.in_(patient_ids)).all()}
    cashiers_map = {u.id: u for u in db.query(User).filter(User.id.in_(cashier_ids)).all()}

    payments_data = [{
        "receipt_number": p.receipt_number,
        "created_at": p.created_at.strftime("%d.%m.%Y %H:%M") if p.created_at else "",
        "patient_name": patients_map.get(p.patient_id, type("", (), {"full_name": "—"})()).full_name,
        "cashier_name": cashiers_map.get(p.cashier_id, type("", (), {"full_name": "—"})()).full_name,
        "payment_method": p.payment_method.value,
        "discount": float(p.discount),
        "total_amount": float(p.total_amount),
        "payment_status": p.payment_status.value
    } for p in payments]

    daily = {}
    for p in payments:
        day = p.created_at.strftime("%d.%m.%Y") if p.created_at else "—"
        if day not in daily:
            daily[day] = {"date": day, "count": 0, "total": 0}
        daily[day]["count"] += 1
        daily[day]["total"] += float(p.total_amount)
    daily_revenue = sorted(daily.values(), key=lambda x: x["date"])

    service_counts: dict = {}
    for p in payments:
        for srv in (p.services_snapshot or []):
            name = srv.get("service_name", "")
            if name not in service_counts:
                service_counts[name] = {"name": name, "count": 0, "revenue": 0}
            service_counts[name]["count"] += int(srv.get("qty", 1))
            service_counts[name]["revenue"] += float(srv.get("price", 0)) * int(srv.get("qty", 1))
    top_services = sorted(service_counts.values(), key=lambda x: x["count"], reverse=True)[:10]

    report_month = f"{month:02d}/{year}"
    buffer = generate_monthly_report_excel(
        clinic_name=clinic.name,
        report_month=report_month,
        payments=payments_data,
        top_services=top_services,
        daily_revenue=daily_revenue
    )

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=hisobot_{report_month.replace('/', '_')}.xlsx"}
    )


# ─── BEMORLAR EXCEL ─────────────────────────────────────────────────────────
@router.get("/patients/excel")
def download_patients_excel(
    clinic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    clinic = ClinicService.get_by_id(db, clinic_id)
    patients = db.query(Patient).filter(
        Patient.clinic_id == clinic_id,
        Patient.is_deleted == False
    ).order_by(Patient.created_at.desc()).all()

    patients_data = [{
        "patient_code": p.patient_code,
        "full_name": p.full_name,
        "birth_date": str(p.birth_date) if p.birth_date else "",
        "gender": p.gender.value if p.gender else "",
        "phone": p.phone,
        "blood_type": p.blood_type.value if p.blood_type else "",
        "allergies": p.allergies,
        "address": p.address,
        "created_at": p.created_at.strftime("%d.%m.%Y") if p.created_at else ""
    } for p in patients]

    buffer = generate_patients_excel(clinic.name, patients_data)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bemorlar.xlsx"}
    )


# ─── NAVBATLAR EXCEL ────────────────────────────────────────────────────────
@router.get("/appointments/excel")
def download_appointments_excel(
    clinic_id: int,
    report_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    check_clinic_access(clinic_id, current_user)
    clinic = ClinicService.get_by_id(db, clinic_id)

    query = db.query(Appointment).filter(Appointment.clinic_id == clinic_id)
    if report_date:
        query = query.filter(Appointment.appointment_date == report_date)
    appointments = query.order_by(Appointment.appointment_date, Appointment.queue_number).all()

    patient_ids = {a.patient_id for a in appointments}
    doctor_ids = {a.doctor_id for a in appointments}
    patients_map = {u.id: u for u in db.query(Patient).filter(Patient.id.in_(patient_ids)).all()}
    doctors_map = {u.id: u for u in db.query(User).filter(User.id.in_(doctor_ids)).all()}

    appt_data = [{
        "queue_number": a.queue_number,
        "appointment_date": str(a.appointment_date),
        "appointment_time": str(a.appointment_time) if a.appointment_time else "",
        "patient_name": patients_map.get(a.patient_id, type("", (), {"full_name": "—"})()).full_name,
        "doctor_name": doctors_map.get(a.doctor_id, type("", (), {"full_name": "—"})()).full_name,
        "visit_reason": a.visit_reason,
        "status": a.status.value
    } for a in appointments]

    buffer = generate_appointments_excel(
        clinic.name, appt_data,
        str(report_date) if report_date else ""
    )
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=navbatlar.xlsx"}
    )