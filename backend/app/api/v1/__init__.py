from fastapi import APIRouter

# Router yaratish
api_router = APIRouter()

# Endpointlarni import qilish va ulash
from app.api.v1.endpoints import auth, users, clinics, patients, appointments, services, payments, notifications, dashboard

# Har bir endpoint routerini asosiy routerga ulash
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clinics.router, prefix="/clinics", tags=["clinics"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])