from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.room import Room

router = APIRouter()

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

    class Config:
        from_attributes = True


@router.get("/", response_model=List[RoomOut])
def read_rooms(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve rooms with pagination.
    """
    rooms = db.query(Room).offset(skip).limit(limit).all()
    return rooms

@router.post("/", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new room.
    """
    db_room = Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.get("/{room_id}", response_model=RoomOut)
def read_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single room by its ID.
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room is None:
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
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    update_data = room.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_room, key, value)
    
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Soft delete a room (sets is_deleted to True).
    """
    db_room = db.query(Room).filter(Room.id == room_id).first()
    if db_room is None or db_room.is_deleted:
        raise HTTPException(status_code=404, detail="Room not found")

    db_room.soft_delete()
    db.commit()
    
    return None