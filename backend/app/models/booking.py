# backend/app/models/booking.py
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import expression

from .base import BaseModel

class Booking(BaseModel):
    __tablename__ = "bookings"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(String(50), nullable=False, default="confirmed")
    purpose = Column(Text)
    guest_count = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='check_end_time_after_start'),
        CheckConstraint('EXTRACT(MINUTE FROM start_time) % 15 = 0', name='check_start_time_interval'),
        CheckConstraint('EXTRACT(MINUTE FROM end_time) % 15 = 0', name='check_end_time_interval'),
        CheckConstraint('guest_count >= 1', name='check_guest_count_positive'),
        
        # Indexes
        Index('ix_bookings_user_id', 'user_id'),
        Index('ix_bookings_room_id', 'room_id'),
        Index('ix_bookings_status', 'status'),
        Index('ix_bookings_time_range', 'room_id', 'start_time', 'end_time'),
        Index('ix_bookings_is_deleted', 'is_deleted'),
        Index('ix_bookings_user_active', 'user_id', 'is_deleted', 'status'),  # For user's active bookings
        
        # Exclusion constraint for overlapping active bookings (excluding soft-deleted)
        # Note: This requires PostgreSQL extension, we'll handle this in application logic
    )
    
    @property
    def is_active_booking(self):
        """Check if booking is active (confirmed and not deleted)"""
        return self.status == "confirmed" and not self.is_deleted
    
    @property
    def duration_minutes(self):
        """Calculate booking duration in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)