from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.booking import Booking
from ...models.room import Room

router = APIRouter()

class BookingCreate(BaseModel):
    """Pydantic model for booking creation."""
    user_id: uuid.UUID
    room_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = None

class BookingUpdate(BaseModel):
    """Pydantic model for booking update."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    purpose: Optional[str] = None

class BookingOut(BaseModel):
    """Pydantic model for booking output."""
    id: uuid.UUID
    user_id: uuid.UUID
    room_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: str
    purpose: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[BookingOut])
def read_bookings(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[uuid.UUID] = None,
    future_only: bool = False
):
    """
    Retrieve bookings with pagination.
    """
    query = db.query(Booking)

    if user_id:
        query = query.filter(Booking.user_id == user_id)
    
    if future_only:
        query = query.filter(Booking.start_time > datetime.utcnow())

    bookings = query.order_by(Booking.start_time.asc()).offset(skip).limit(limit).all()
    return bookings

@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new booking.
    """
    room = db.query(Room).filter(Room.id == booking.room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=404, detail="Active room not found")
    
    overlapping_booking = db.query(Booking).filter(
        Booking.room_id == booking.room_id,
        Booking.end_time > booking.start_time,
        Booking.start_time < booking.end_time,
        Booking.status == 'confirmed',
        Booking.is_deleted == False
    ).first()

    if overlapping_booking:
        raise HTTPException(status_code=409, detail="Booking conflict: The room is already booked for the requested time.")

    db_booking = Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@router.get("/{booking_id}", response_model=BookingOut)
def read_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single booking by its ID.
    """
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking

@router.put("/{booking_id}", response_model=BookingOut)
def update_booking(
    booking_id: uuid.UUID,
    booking: BookingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing booking.
    """
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    update_data = booking.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_booking, key, value)
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Soft delete a booking (sets is_deleted to True and status to 'cancelled').
    """
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.is_deleted:
        raise HTTPException(status_code=404, detail="Booking not found")

    db_booking.soft_delete()
    db_booking.status = "cancelled"
    db.commit()
    
    return None