from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from sqlalchemy.orm import relationship

from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(255))
    
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    avatar_url = Column(Text)
    phone = Column(String(50))
    preferred_timezone = Column(String(50), default="UTC")
    
    last_login = Column(DateTime(timezone=True))
    
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_users_email', 'email'),
        Index('ix_users_username', 'username'),
        Index('ix_users_is_active', 'is_active'),
        Index('ix_users_is_deleted', 'is_deleted'),
    )