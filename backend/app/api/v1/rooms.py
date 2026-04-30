from typing import List, Optional
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.room import RoomCreate, RoomOut, RoomUpdate
from ... import crud

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[RoomOut])
def read_rooms(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    coworking_space_id: Optional[uuid.UUID] = None
):
    """
    Retrieve rooms with pagination.
    """
    logger.info(f"GET rooms (coworking_space_id={coworking_space_id}, skip={skip}, limit={limit})")
    if coworking_space_id:
        rooms = crud.room.get_multi_by_space(
            db, coworking_space_id=coworking_space_id, skip=skip, limit=limit
        )
    else:
        rooms = crud.room.get_multi(db, skip=skip, limit=limit)
    logger.info(f"GET success - {len(rooms)} rooms")
    return rooms

@router.post("/", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new room.
    """
    logger.info(f"POST create room with name: {room.name}")
    db_room = crud.room.create(db=db, obj_in=room)
    logger.info(f"POST success - created room with ID: {db_room.id}")
    return db_room

@router.get("/{room_id}", response_model=RoomOut)
def read_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single room by its ID.
    """
    logger.info(f"GET single room with ID: {room_id}")
    db_room = crud.room.get(db, id=room_id)
    if db_room is None:
        logger.warning(f"GET warn - room {room_id} not found")
        raise HTTPException(status_code=404, detail="Room not found")
    return db_room

@router.put("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: uuid.UUID,
    room: RoomUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing room.
    """
    logger.info(f"PUT update room {room_id}")
    db_room = crud.room.get(db, id=room_id)
    if db_room is None:
        logger.warning(f"PUT warn - room {room_id} not found for update")
        raise HTTPException(status_code=404, detail="Room not found")
    
    db_room = crud.room.update(db=db, db_obj=db_room, obj_in=room)
    logger.info(f"PUT success - updated room {room_id}")
    return db_room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Soft delete a room (sets is_deleted to True).
    """
    logger.info(f"DELETE soft deleting room {room_id}")
    db_room = crud.room.get(db, id=room_id)
    if db_room is None or db_room.is_deleted:
        logger.warning(f"DELETE warn - room {room_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Room not found")

    crud.room.soft_remove(db=db, db_obj=db_room)
    logger.info(f"DELETE success - deleted room {room_id}")
    return None