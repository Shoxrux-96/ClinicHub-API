from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== NOTIFICATION ENUMS ====================

class NotificationType(str, Enum):
    """Bildirishnoma turlari"""
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    PAYMENT = "payment"
    SYSTEM = "system"
    ALERT = "alert"
    MESSAGE = "message"
    PROMOTION = "promotion"
    UPDATE = "update"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"


class NotificationStatus(str, Enum):
    """Bildirishnoma holati"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Bildirishnoma prioriteti"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """Bildirishnoma kanali"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"


# ==================== NOTIFICATION BASE SCHEMAS ====================

class NotificationBase(BaseModel):
    """Asosiy notification schema"""
    user_id: int = Field(..., description="User ID")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(..., min_length=1, max_length=1000, description="Notification message")
    type: NotificationType = Field(NotificationType.SYSTEM, description="Notification type")
    priority: NotificationPriority = Field(NotificationPriority.NORMAL, description="Priority")
    channel: NotificationChannel = Field(NotificationChannel.IN_APP, description="Channel")
    is_read: bool = Field(False, description="Is notification read")
    action_url: Optional[str] = Field(None, max_length=500, description="Action URL")
    image_url: Optional[str] = Field(None, max_length=500, description="Image URL")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    class Config:
        use_enum_values = True


class NotificationCreate(NotificationBase):
    """Bildirishnoma yaratish uchun schema"""
    scheduled_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    retry_count: int = Field(0, ge=0, le=5)
    
    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        if v and v < datetime.now():
            raise ValueError('Scheduled time cannot be in the past')
        return v


class NotificationUpdate(BaseModel):
    """Bildirishnoma yangilash uchun schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1, max_length=1000)
    is_read: Optional[bool] = None
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


# ==================== NOTIFICATION RESPONSE SCHEMAS ====================

class NotificationResponse(NotificationBase):
    """Bildirishnoma javob schemasi"""
    id: int
    status: NotificationStatus = NotificationStatus.PENDING
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class NotificationListResponse(BaseModel):
    """Bildirishnomalar ro'yxati javobi"""
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    size: int
    pages: int


# ==================== NOTIFICATION FILTERS ====================

class NotificationFilter(BaseModel):
    """Bildirishnoma filtrlari"""
    user_id: Optional[int] = None
    type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    priority: Optional[NotificationPriority] = None
    channel: Optional[NotificationChannel] = None
    is_read: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = Field(None, description="Search by title or message")
    
    class Config:
        use_enum_values = True


# ==================== EMAIL NOTIFICATION ====================

class EmailNotification(NotificationBase):
    """Email bildirishnoma"""
    email: str = Field(..., description="Recipient email")
    subject: str = Field(..., max_length=255, description="Email subject")
    html_content: Optional[str] = Field(None, description="HTML content")
    attachments: List[dict] = Field(default_factory=list, description="Email attachments")


# ==================== SMS NOTIFICATION ====================

class SMSNotification(NotificationBase):
    """SMS bildirishnoma"""
    phone_number: str = Field(..., description="Recipient phone number")
    sender: Optional[str] = Field(None, max_length=20, description="Sender name")


# ==================== PUSH NOTIFICATION ====================

class PushNotification(NotificationBase):
    """Push bildirishnoma"""
    device_token: str = Field(..., description="Device token")
    platform: str = Field(..., description="Platform (ios, android, web)")
    badge_count: Optional[int] = Field(None, description="Badge count")
    sound: Optional[str] = Field(None, description="Notification sound")
    click_action: Optional[str] = Field(None, description="Click action")


# ==================== NOTIFICATION STATISTICS ====================

class NotificationStats(BaseModel):
    """Bildirishnoma statistikasi"""
    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    read_notifications: int
    failed_notifications: int
    pending_notifications: int
    notifications_by_type: dict = Field(default_factory=dict)
    notifications_by_priority: dict = Field(default_factory=dict)
    notifications_by_channel: dict = Field(default_factory=dict)
    daily_stats: List[dict] = Field(default_factory=list)


# ==================== NOTIFICATION TEMPLATE ====================

class NotificationTemplate(BaseModel):
    """Bildirishnoma shabloni"""
    id: int
    name: str
    type: NotificationType
    subject: Optional[str] = None
    template: str
    variables: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime