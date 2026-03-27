from pydantic import BaseModel
import uuid

class RoomOut(BaseModel):
    """Pydantic model for room output."""
    id: uuid.UUID
    name: str
    capacity: int
    is_active: bool
    coworking_space_id: uuid.UUID

    class Config:
        from_attributes = True