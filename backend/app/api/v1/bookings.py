from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.booking import BookingCreate, BookingOut, BookingUpdate
from ... import crud

router = APIRouter()


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
    if user_id:
        bookings = crud.booking.get_multi_by_user(
            db, user_id=user_id, future_only=future_only, skip=skip, limit=limit
        )
    else:
        bookings = crud.booking.get_multi(db, skip=skip, limit=limit)
    return bookings

@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new booking.
    """
    db_booking = crud.booking.create_with_overlap_check(db=db, obj_in=booking)
    return db_booking

@router.get("/{booking_id}", response_model=BookingOut)
def read_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single booking by its ID.
    """
    db_booking = crud.booking.get(db, id=booking_id)
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
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    db_booking = crud.booking.update(db=db, db_obj=db_booking, obj_in=booking)
    return db_booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Soft delete a booking (sets is_deleted to True and status to 'cancelled').
    """
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.is_deleted:
        raise HTTPException(status_code=404, detail="Booking not found")

    crud.booking.soft_remove_with_status(db=db, db_obj=db_booking)
    
    return None