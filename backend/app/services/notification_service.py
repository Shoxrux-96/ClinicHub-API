from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationStatus


class NotificationService:
    """Bildirishnomalar uchun service"""

    @staticmethod
    def get_notifications(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        type: Optional[str] = None,
        is_read: Optional[bool] = None
    ) -> List[Notification]:
        """Foydalanuvchi bildirishnomalarini olish"""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if type:
            query = query.filter(Notification.type == type)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]:
        """ID bo'yicha bildirishnoma olish"""
        return db.query(Notification).filter(Notification.id == notification_id).first()

    @staticmethod
    def create_notification(db: Session, notification_data: NotificationCreate) -> Notification:
        """Yangi bildirishnoma yaratish"""
        notification = Notification(
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type,
            priority=notification_data.priority,
            channel=notification_data.channel,
            action_url=notification_data.action_url,
            metadata=notification_data.metadata,
            is_read=False,
            status="pending"
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """Bildirishnomani o'qilgan deb belgilash"""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            return None

        notification.is_read = True
        notification.read_at = datetime.now()
        notification.status = "read"
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Barcha bildirishnomalarni o'qilgan deb belgilash"""
        result = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update(
            {"is_read": True, "read_at": datetime.now(), "status": "read"},
            synchronize_session=False
        )
        db.commit()
        return result

    @staticmethod
    def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
        """Bildirishnomani o'chirish"""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            return False

        db.delete(notification)
        db.commit()
        return True

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """O'qilmagan bildirishnomalar sonini olish"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

    @staticmethod
    def update_status(db: Session, notification_id: int, status: str) -> Optional[Notification]:
        """Bildirishnoma holatini yangilash"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return None

        notification.status = status
        if status == "sent":
            notification.sent_at = datetime.now()
        elif status == "delivered":
            notification.delivered_at = datetime.now()

        db.commit()
        db.refresh(notification)
        return notification