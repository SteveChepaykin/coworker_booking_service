from typing import List

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.space import SpaceOut
from ... import crud

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[SpaceOut])
def read_spaces(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all active coworking spaces with pagination.
    """
    logger.info(f"GET active spaces (skip={skip}, limit={limit})")
    spaces = crud.space.get_multi_active(db, skip=skip, limit=limit)
    logger.info(f"GET success - {len(spaces)} active spaces")
    return spaces