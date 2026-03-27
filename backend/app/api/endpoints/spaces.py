from typing import List
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.coworking_space import CoworkingSpace

router = APIRouter()

class CoworkingSpaceOut(BaseModel):
    """Pydantic model for coworking space output."""
    id: uuid.UUID
    name: str
    address: str
    city: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CoworkingSpaceOut])
def read_spaces(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Retrieve all coworking spaces."""
    spaces = db.query(CoworkingSpace).offset(skip).limit(limit).all()
    return spaces