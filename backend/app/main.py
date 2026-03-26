from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from app.core.database import engine, SessionLocal
from app.core.config import settings
from app.api.v1 import api_router
from app.services.auth_service import AuthService
import os

# Database modellarni import qilish
from app.models import user, clinic, patient, appointment, service, payment, notification

# Create tables
def create_tables():
    """Create database tables"""
    try:
        # Barcha modellarni import qilish va tablizalarni yaratish
        from app.models.base import Base
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")

# Lifespan context manager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    print("Starting up...")
    
    # Create tables
    create_tables()
    
    # Create first owner
    db = SessionLocal()
    try:
        AuthService.create_first_owner(db)
    finally:
        db.close()
    
    yield
    
    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="ClinicHub API",
    description="Clinic Management System API",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI manzili
    redoc_url="/redoc",  # ReDoc manzili
    openapi_url="/openapi.json"  # OpenAPI schema manzili
)

# CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production da aniq domainlar qo'ying
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routerlarni ulash
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to ClinicHub API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"  # Database connection status
    }