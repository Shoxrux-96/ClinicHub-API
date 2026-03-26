from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class TimestampMixin:
    """Vaqt belgilari uchun mixin"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class SoftDeleteMixin:
    """Yumshoq o'chirish uchun mixin"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)