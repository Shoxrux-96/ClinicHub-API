from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.core.database import get_db
from app.core.security import get_current_user, get_current_owner
from app.schemas.service import (
    ServiceCreate, ServiceUpdate, ServiceResponse,
    ServiceCategory, ServicePricing, ServiceStats
)
from app.services.service_service import ServiceService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[ServiceResponse])
def get_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    clinic_id: Optional[int] = Query(None, description="Filter by clinic"),
    category: Optional[ServiceCategory] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all services with filters
    """
    # Foydalanuvchi o'z klinikasining xizmatlarini ko'ra oladi
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id:
            services = ServiceService.get_services(
                db, skip=skip, limit=limit,
                clinic_id=current_user.clinic_id, category=category,
                is_active=is_active, search=search
            )
            return services
        return []
    
    services = ServiceService.get_services(
        db, skip=skip, limit=limit,
        clinic_id=clinic_id, category=category,
        is_active=is_active, search=search
    )
    return services


@router.get("/stats", response_model=ServiceStats)
def get_services_stats(
    clinic_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get services statistics (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return ServiceService.get_services_stats(db, clinic_id)


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get service by ID
    """
    service = ServiceService.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != service.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return service


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    service_data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new service (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can create services"
        )
    
    # Klinika ID sini o'rnatish
    if not current_user.is_superuser and current_user.clinic_id:
        service_data.clinic_id = current_user.clinic_id
    
    service = ServiceService.create_service(db, service_data)
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update service (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can update services"
        )
    
    service = ServiceService.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_superuser:
        if current_user.clinic_id != service.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    updated_service = ServiceService.update_service(db, service_id, service_data)
    return updated_service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete service (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete services"
        )
    
    service = ServiceService.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_superuser:
        if current_user.clinic_id != service.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    success = ServiceService.delete_service(db, service_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # 204 status code da hech narsa qaytarmaymiz
    return None


@router.get("/{service_id}/pricing", response_model=ServicePricing)
def get_service_pricing(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get service pricing details
    """
    pricing = ServiceService.get_pricing(db, service_id)
    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    return pricing


@router.patch("/{service_id}/toggle-active", response_model=ServiceResponse)
def toggle_service_active(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Toggle service active status (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can modify service status"
        )
    
    service = ServiceService.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Ruxsatni tekshirish
    if not current_user.is_superuser:
        if current_user.clinic_id != service.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    service.is_active = not service.is_active
    db.commit()
    db.refresh(service)
    return service


@router.get("/clinic/{clinic_id}/services", response_model=List[ServiceResponse])
def get_clinic_services(
    clinic_id: int,
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get services by clinic ID
    """
    # Ruxsatni tekshirish
    if not current_user.is_owner and not current_user.is_superuser:
        if current_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    services = ServiceService.get_services(
        db, clinic_id=clinic_id, is_active=is_active
    )
    return services