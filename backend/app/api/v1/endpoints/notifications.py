from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.notification import (
    NotificationCreate, NotificationResponse,
    NotificationType, NotificationStatus
)
from app.services.notification_service import NotificationService
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    type: Optional[NotificationType] = Query(None, description="Filter by type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all notifications for current user
    """
    notifications = NotificationService.get_notifications(
        db, user_id=current_user.id, skip=skip, limit=limit,
        type=type, is_read=is_read
    )
    return notifications


@router.get("/unread-count", response_model=dict)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get unread notifications count
    """
    count = NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get notification by ID
    """
    notification = NotificationService.get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Check permission
    if notification.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return notification


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new notification (Admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create notifications"
        )
    
    notification = NotificationService.create_notification(db, notification_data)
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Mark notification as read
    """
    notification = NotificationService.mark_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.patch("/read-all", response_model=dict)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Mark all notifications as read
    """
    count = NotificationService.mark_all_as_read(db, current_user.id)
    return {"marked_count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete notification
    """
    notification = NotificationService.get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Check permission
    if notification.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    success = NotificationService.delete_notification(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # 204 status code da hech narsa qaytarmaymiz
    return None


@router.post("/send-email")
def send_email_notification(
    user_id: int,
    subject: str,
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Send email notification (Admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send email notifications"
        )
    
    # Email yuborish logikasi
    notification = NotificationService.create_notification(
        db, NotificationCreate(
            user_id=user_id,
            title=subject,
            message=message,
            type=NotificationType.EMAIL,
            channel="email"
        )
    )
    
    return {"message": "Email notification sent", "notification_id": notification.id}


@router.post("/send-sms")
def send_sms_notification(
    user_id: int,
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Send SMS notification (Admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send SMS notifications"
        )
    
    # SMS yuborish logikasi
    notification = NotificationService.create_notification(
        db, NotificationCreate(
            user_id=user_id,
            title="SMS",
            message=message,
            type=NotificationType.SMS,
            channel="sms"
        )
    )
    
    return {"message": "SMS notification sent", "notification_id": notification.id}


@router.get("/types/all", response_model=List[str])
def get_notification_types(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all notification types
    """
    return [t.value for t in NotificationType]


@router.get("/status/all", response_model=List[str])
def get_notification_statuses(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all notification statuses
    """
    return [s.value for s in NotificationStatus]