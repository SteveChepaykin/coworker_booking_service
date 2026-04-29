from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.coworking_space import CoworkingSpace
from ...schemas.space import SpaceOut

router = APIRouter()

@router.get("/", response_model=List[SpaceOut])
def read_spaces(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all active coworking spaces with pagination.
    """
    spaces = db.query(CoworkingSpace).filter(CoworkingSpace.is_active == True).offset(skip).limit(limit).all()
    return spaces