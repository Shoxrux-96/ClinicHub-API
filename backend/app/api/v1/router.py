from fastapi import APIRouter
from app.api.v1 import (
    auth, clinics, users, patients,
    appointments, medical_records,
    lab_results, services, payments, reports
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(clinics.router)
api_router.include_router(users.router)
api_router.include_router(patients.router)
api_router.include_router(appointments.router)
api_router.include_router(medical_records.router)
api_router.include_router(lab_results.router)
api_router.include_router(services.router)
api_router.include_router(payments.router)
api_router.include_router(reports.router)