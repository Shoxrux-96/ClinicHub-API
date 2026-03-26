from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceStats


class ServiceService:
    """Xizmatlar uchun service"""

    @staticmethod
    def get_services(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        clinic_id: Optional[int] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Service]:
        """Xizmatlar ro'yxatini olish"""
        query = db.query(Service)

        if clinic_id:
            query = query.filter(Service.clinic_id == clinic_id)
        if category:
            query = query.filter(Service.category == category)
        if is_active is not None:
            query = query.filter(Service.is_active == is_active)
        if search:
            query = query.filter(Service.name.ilike(f"%{search}%"))

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_service_by_id(db: Session, service_id: int) -> Optional[Service]:
        """ID bo'yicha xizmat olish"""
        return db.query(Service).filter(Service.id == service_id).first()

    @staticmethod
    def create_service(db: Session, service_data: ServiceCreate) -> Service:
        """Yangi xizmat yaratish"""
        service = Service(
            name=service_data.name,
            description=service_data.description,
            category=service_data.category,
            price=service_data.price,
            duration=service_data.duration,
            clinic_id=service_data.clinic_id,
            is_active=True
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        return service

    @staticmethod
    def update_service(
        db: Session,
        service_id: int,
        service_data: ServiceUpdate
    ) -> Optional[Service]:
        """Xizmat ma'lumotlarini yangilash"""
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return None

        update_data = service_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(service, field, value)

        db.commit()
        db.refresh(service)
        return service

    @staticmethod
    def delete_service(db: Session, service_id: int) -> bool:
        """Xizmatni o'chirish"""
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return False

        db.delete(service)
        db.commit()
        return True

    @staticmethod
    def get_pricing(db: Session, service_id: int) -> Optional[dict]:
        """Xizmat narxini olish"""
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            return None

        return {
            "service_id": service.id,
            "service_name": service.name,
            "base_price": service.price,
            "current_price": service.price,
            "discount_percentage": 0,
            "discount_amount": 0
        }

    @staticmethod
    def get_services_stats(db: Session, clinic_id: Optional[int] = None) -> ServiceStats:
        """Xizmatlar statistikasi"""
        query = db.query(Service)
        if clinic_id:
            query = query.filter(Service.clinic_id == clinic_id)

        total_services = query.count()
        active_services = query.filter(Service.is_active == True).count()

        from sqlalchemy import func
        services_by_category = db.query(
            Service.category,
            func.count(Service.id)
        ).group_by(Service.category).all()

        return ServiceStats(
            total_services=total_services,
            active_services=active_services,
            inactive_services=total_services - active_services,
            services_by_category=dict(services_by_category),
            total_revenue=0,
            average_price=0
        )