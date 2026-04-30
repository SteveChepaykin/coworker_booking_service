from datetime import datetime
from typing import List, Optional
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.booking import BookingCreate, BookingOut, BookingUpdate
from ... import crud

router = APIRouter()
logger = logging.getLogger(__name__)


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
    logger.info(f"GET bookings (user_id={user_id}, future_only={future_only})")
    if user_id:
        bookings = crud.booking.get_multi_by_user(
            db, user_id=user_id, future_only=future_only, skip=skip, limit=limit
        )
    else:
        bookings = crud.booking.get_multi(db, skip=skip, limit=limit)
    logger.info(f"GET success - {len(bookings)} bookings")
    return bookings

@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new booking.
    """
    logger.info(f"POST booking for room: {booking.room_id} by user: {booking.user_id}")
    db_booking = crud.booking.create_with_overlap_check(db=db, obj_in=booking)
    logger.info(f"POST success - created booking with ID: {db_booking.id}")
    return db_booking

@router.get("/{booking_id}", response_model=BookingOut)
def read_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single booking by its ID.
    """
    logger.info(f"GET single booking with ID: {booking_id}")
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        logger.warning(f"GET warn - {booking_id} not found")
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
    logger.info(f"PUT update booking {booking_id}")
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        logger.warning(f"PUT warn - {booking_id} not found for update")
        raise HTTPException(status_code=404, detail="Booking not found")

    db_booking = crud.booking.update(db=db, db_obj=db_booking, obj_in=booking)
    logger.info(f"PUT success - updated booking {booking_id}")
    return db_booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Soft delete a booking (sets is_deleted to True and status to 'cancelled').
    """
    logger.info(f"DELETE soft deleting booking {booking_id}")
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        logger.warning(f"DELETE warn - {booking_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if db_booking.is_deleted:
        logger.warning(f"DELETE warn - {booking_id} is already deleted")
        raise HTTPException(status_code=404, detail="Booking not found")

    crud.booking.soft_remove_with_status(db=db, db_obj=db_booking)
    logger.info(f"DELETE success - deleted booking {booking_id}")
    
    return None