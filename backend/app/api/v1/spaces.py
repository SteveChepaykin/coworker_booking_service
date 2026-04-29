from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.space import SpaceOut
from ... import crud

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
    spaces = crud.space.get_multi_active(db, skip=skip, limit=limit)
    return spaces