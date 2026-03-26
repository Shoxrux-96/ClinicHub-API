from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric, Text, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum
from sqlalchemy import Enum as SAEnum


class ServiceCategory(str, enum.Enum):
    """Xizmat kategoriyalari"""
    CONSULTATION = "consultation"      # Konsultatsiya
    DIAGNOSTIC = "diagnostic"          # Diagnostika
    LABORATORY = "laboratory"          # Laboratoriya
    RADIOLOGY = "radiology"            # Rentgen/UZI
    SURGERY = "surgery"                # Jarrohlik
    DENTAL = "dental"                  # Stomatologiya
    VACCINATION = "vaccination"        # Emlash
    PHYSIOTHERAPY = "physiotherapy"    # Fizioterapiya
    WELLNESS = "wellness"              # Wellness
    OTHER = "other"                    # Boshqa


class Service(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "services"
    
    # Indekslar
    __table_args__ = (
        Index('idx_service_clinic_active', 'clinic_id', 'is_active'),
        Index('idx_service_category', 'category'),
        Index('idx_service_name', 'name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, index=True)
    
    # Asosiy ma'lumotlar
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Narx va vaqt
    price = Column(Numeric(12, 2), nullable=False, default=0)
    duration_minutes = Column(Integer, default=30)  # xizmat davomiyligi
    
    # Chegirma
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_start_date = Column(DateTime(timezone=True), nullable=True)
    discount_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Xizmat xususiyatlari
    is_active = Column(Boolean, default=True, index=True)
    requires_doctor = Column(Boolean, default=True)
    requires_referral = Column(Boolean, default=False)
    insurance_accepted = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    
    # Qo'shimcha ma'lumotlar
    preparation_instructions = Column(Text, nullable=True)  # Tayyorgarlik
    aftercare_instructions = Column(Text, nullable=True)    # Keyingi parvarish
    notes = Column(Text, nullable=True)
    
    # Statistika
    total_bookings = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2), default=0)
    total_reviews = Column(Integer, default=0)
    
    # Qo'shimcha
    image_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0)
    
    # Relationships
    clinic = relationship("Clinic", back_populates="services")
    appointments = relationship("Appointment", back_populates="service", cascade="all, delete-orphan")
    
    # ==================== Methods ====================
    
    def get_current_price(self) -> float:
        """Chegirma bilan joriy narxni olish"""
        from datetime import datetime
        
        if self.discount_percentage and self.discount_percentage > 0:
            if self.discount_start_date and self.discount_end_date:
                now = datetime.now()
                if self.discount_start_date <= now <= self.discount_end_date:
                    discount_amount = float(self.price) * (float(self.discount_percentage) / 100)
                    return float(self.price) - discount_amount
        
        return float(self.price)
    
    def get_discount_amount(self) -> float:
        """Chegirma miqdorini olish"""
        return float(self.price) - self.get_current_price()
    
    def is_discount_active(self) -> bool:
        """Chegirma aktivligini tekshirish"""
        from datetime import datetime
        
        if not self.discount_percentage or self.discount_percentage <= 0:
            return False
        
        if self.discount_start_date and self.discount_end_date:
            now = datetime.now()
            return self.discount_start_date <= now <= self.discount_end_date
        
        return False
    
    def is_available(self) -> bool:
        """Xizmat mavjudligini tekshirish"""
        return self.is_active
    
    def increment_bookings(self):
        """Xizmat bandligini oshirish"""
        self.total_bookings += 1
    
    def update_rating(self, new_rating: int):
        """O'rtacha reytingni yangilash"""
        total = (self.average_rating * self.total_reviews) + new_rating
        self.total_reviews += 1
        self.average_rating = total / self.total_reviews
    
    def get_duration_hours(self) -> float:
        """Davomiylikni soatlarda olish"""
        return self.duration_minutes / 60
    
    def get_price_per_hour(self) -> float:
        """Soatlik narxni olish"""
        if self.duration_minutes > 0:
            return (float(self.price) / self.duration_minutes) * 60
        return float(self.price)
    
    def to_dict(self) -> dict:
        """Ob'ektni dictionary ga o'zgartirish"""
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": float(self.price),
            "current_price": self.get_current_price(),
            "discount_percentage": float(self.discount_percentage) if self.discount_percentage else 0,
            "is_discount_active": self.is_discount_active(),
            "duration_minutes": self.duration_minutes,
            "is_active": self.is_active,
            "requires_doctor": self.requires_doctor,
            "requires_referral": self.requires_referral,
            "insurance_accepted": self.insurance_accepted,
            "preparation_instructions": self.preparation_instructions,
            "aftercare_instructions": self.aftercare_instructions,
            "total_bookings": self.total_bookings,
            "average_rating": float(self.average_rating) if self.average_rating else 0,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Service {self.id}: {self.name} - {self.price}>"