from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.core.database import get_db
from app.core.security import get_current_user, get_current_superuser
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, 
    UserDetailResponse, UserFilter, UserListResponse
)
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(100, ge=1, le=1000, description="Limit records"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all users with pagination and filters
    """
    # Owner va superuser barcha foydalanuvchilarni ko'ra oladi
    # Boshqa foydalanuvchilar faqat o'zini ko'ra oladi
    if not current_user.is_owner and not current_user.is_superuser:
        # Oddiy foydalanuvchi faqat o'zini ko'radi
        return [current_user]
    
    users = UserService.get_users(
        db, skip=skip, limit=limit, 
        search=search, role=role, is_active=is_active
    )
    return users


@router.get("/list", response_model=UserListResponse)
def get_users_list(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    filter: Optional[UserFilter] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get paginated users list
    """
    if not current_user.is_owner and not current_user.is_superuser:
        return UserListResponse(
            items=[current_user],
            total=1,
            page=page,
            size=size,
            pages=1
        )
    
    return UserService.get_users_paginated(db, page=page, size=size, filter=filter)


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get user by ID with detailed information
    """
    # Foydalanuvchi o'z ma'lumotlarini yoki admin/owner boshqalarni ko'ra oladi
    if user_id != current_user.id and not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user"
        )
    
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new user
    """
    # Faqat owner va superuser yangi foydalanuvchi yarata oladi
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and superusers can create users"
        )
    
    # Email mavjudligini tekshirish
    existing_user = UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = UserService.create_user(db, user_data)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update user information
    """
    # Foydalanuvchi o'z ma'lumotlarini yoki admin/owner boshqalarni yangilay oladi
    if user_id != current_user.id and not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user"
        )
    
    user = UserService.update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Activate user (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and superusers can activate users"
        )
    
    user = UserService.activate_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Deactivate user (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and superusers can deactivate users"
        )
    
    # O'zini o'chirolmaydi
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate yourself"
        )
    
    user = UserService.deactivate_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete user (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and superusers can delete users"
        )
    
    # O'zini o'chira olmaydi
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself"
        )
    
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 204 status code da hech narsa qaytarmaymiz
    return None


@router.get("/me/profile", response_model=UserDetailResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user profile
    """
    return current_user


@router.patch("/me/profile", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update current user profile
    """
    user = UserService.update_user(db, current_user.id, user_data)
    return user


@router.get("/stats/summary")
def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get user statistics (Admin/Owner only)
    """
    if not current_user.is_owner and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and superusers can view statistics"
        )
    
    return UserService.get_user_statistics(db)