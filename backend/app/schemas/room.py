from pydantic import BaseModel
import uuid
from typing import Optional

class RoomCreate(BaseModel):
    """Pydantic model for room creation."""
    name: str
    capacity: int
    coworking_space_id: uuid.UUID

class RoomUpdate(BaseModel):
    """Pydantic model for room update."""
    name: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None

class RoomOut(BaseModel):
    """Pydantic model for room output."""
    id: uuid.UUID
    name: str
    capacity: int
    is_active: bool
    coworking_space_id: uuid.UUID

    class Config:
        from_attributes = True