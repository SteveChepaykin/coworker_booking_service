from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel

class BookingCreate(BaseModel):
    """Pydantic model for booking creation."""
    user_id: uuid.UUID
    room_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None

class BookingUpdate(BaseModel):
    """Pydantic model for booking update."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    purpose: Optional[str] = None

class BookingOut(BaseModel):
    """Pydantic model for booking output."""
    id: uuid.UUID
    user_id: uuid.UUID
    room_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: str
    purpose: Optional[str] = None

    class Config:
        from_attributes = True