from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime


class NotificationType(str, enum.Enum):
    """Bildirishnoma turlari"""
    APPOINTMENT = "appointment"      # Uchrashuv
    REMINDER = "reminder"            # Eslatma
    PAYMENT = "payment"              # To'lov
    SYSTEM = "system"                # Tizim
    ALERT = "alert"                  # Ogohlantirish
    MESSAGE = "message"              # Xabar
    PROMOTION = "promotion"          # Aksiya
    UPDATE = "update"                # Yangilanish
    LAB_RESULT = "lab_result"        # Laboratoriya natijasi
    PRESCRIPTION = "prescription"    # Retsept


class NotificationStatus(str, enum.Enum):
    """Bildirishnoma holati"""
    PENDING = "pending"              # Kutilmoqda
    SENT = "sent"                    # Yuborilgan
    DELIVERED = "delivered"          # Yetkazilgan
    READ = "read"                    # O'qilgan
    FAILED = "failed"                # Muvaffaqiyatsiz
    CANCELLED = "cancelled"          # Bekor qilingan


class NotificationPriority(str, enum.Enum):
    """Bildirishnoma prioriteti"""
    LOW = "low"                      # Past
    NORMAL = "normal"                # Normal
    HIGH = "high"                    # Yuqori
    URGENT = "urgent"                # Shoshilinch


class NotificationChannel(str, enum.Enum):
    """Bildirishnoma kanali"""
    EMAIL = "email"                  # Elektron pochta
    SMS = "sms"                      # SMS
    PUSH = "push"                    # Push-bildirishnoma
    IN_APP = "in_app"                # Ilova ichida
    WHATSAPP = "whatsapp"            # WhatsApp


class Notification(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "notifications"
    
    # Indekslar
    __table_args__ = (
        Index('idx_notification_user', 'user_id'),
        Index('idx_notification_clinic', 'clinic_id'),
        Index('idx_notification_status', 'status'),
        Index('idx_notification_type', 'type'),
        Index('idx_notification_created', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=True, index=True)
    
    # Bildirishnoma ma'lumotlari
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SAEnum(NotificationType), default=NotificationType.SYSTEM, nullable=False)
    priority = Column(SAEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=True)
    channel = Column(SAEnum(NotificationChannel), default=NotificationChannel.IN_APP, nullable=True)
    
    # Holat
    status = Column(SAEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Vaqt
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Qo'shimcha
    action_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    extra_data = Column(JSON, nullable=True)  # metadata o'rniga extra_data (metadata rezerv qilingan)
    retry_count = Column(Integer, default=0)
    
    # SMS uchun
    phone_number = Column(String(20), nullable=True)
    
    # Email uchun
    email = Column(String(255), nullable=True)
    email_subject = Column(String(255), nullable=True)
    email_html = Column(Text, nullable=True)
    
    # Push uchun
    device_token = Column(String(500), nullable=True)
    platform = Column(String(50), nullable=True)  # ios, android, web
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    clinic = relationship("Clinic", back_populates="notifications")
    
    # ==================== Methods ====================
    
    def mark_as_read(self):
        """O'qilgan deb belgilash"""
        self.is_read = True
        self.read_at = datetime.now()
        self.status = NotificationStatus.READ
    
    def mark_as_sent(self):
        """Yuborilgan deb belgilash"""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
    
    def mark_as_delivered(self):
        """Yetkazilgan deb belgilash"""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_as_failed(self):
        """Muvaffaqiyatsiz deb belgilash"""
        self.status = NotificationStatus.FAILED
    
    def is_expired(self) -> bool:
        """Muddati o'tganligini tekshirish"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def can_send(self) -> bool:
        """Yuborish mumkinligini tekshirish"""
        if self.is_expired():
            return False
        if self.status not in [NotificationStatus.PENDING, NotificationStatus.FAILED]:
            return False
        if self.scheduled_time and datetime.now() < self.scheduled_time:
            return False
        return True
    
    def increment_retry(self):
        """Qayta urinishlar sonini oshirish"""
        self.retry_count += 1
        if self.retry_count >= 3:
            self.mark_as_failed()
    
    def to_dict(self) -> dict:
        """Ob'ektni dictionary ga o'zgartirish"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "clinic_id": self.clinic_id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value if self.type else None,
            "priority": self.priority.value if self.priority else None,
            "channel": self.channel.value if self.channel else None,
            "status": self.status.value if self.status else None,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "action_url": self.action_url,
            "image_url": self.image_url,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Notification {self.id}: {self.title}>"