from pydantic import BaseModel
import uuid
from typing import Optional

class SpaceOut(BaseModel):
    """Pydantic model for coworking space output."""
    id: uuid.UUID
    name: str
    address: str
    city: str
    image_link: Optional[str] = None

    class Config:
        from_attributes = True