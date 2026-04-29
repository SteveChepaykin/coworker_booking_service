from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel

class CoworkingSpace(BaseModel):
    __tablename__ = "coworking_spaces"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)

    rooms = relationship("Room", back_populates="coworking_space", cascade="all, delete-orphan")