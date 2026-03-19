# backend/app/models/room.py
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel

class Room(BaseModel):
    __tablename__ = "rooms"

    coworking_space_id = Column(UUID(as_uuid=True), ForeignKey("coworking_spaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    coworking_space = relationship("CoworkingSpace", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")