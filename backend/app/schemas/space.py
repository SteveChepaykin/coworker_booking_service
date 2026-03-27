from pydantic import BaseModel
import uuid

class SpaceOut(BaseModel):
    """Pydantic model for coworking space output."""
    id: uuid.UUID
    name: str
    address: str
    city: str

    class Config:
        from_attributes = True