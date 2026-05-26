from datetime import date
from typing import List, Optional, Union
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.redis import redis_client
from ...schemas.booking import BookingCreate, BookingOut, BookingUpdate
from ... import crud
from ..deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def _invalidate_user_bookings_cache(user_id: str):
    """
    Invalidate all cache entries for a user's booking list.
    This uses SCAN to find all variations of the booking list URL (with different
    query parameters) and deletes them, ensuring the user always sees fresh data
    after making a change.
    """
    if redis_client:
        match_pattern = f"cache:req:{user_id}:/api/v1/bookings/?*"
        logger.info(f"Scanning for cache keys to invalidate with pattern: {match_pattern}")
        
        keys_to_delete = [key for key in redis_client.scan_iter(match=match_pattern)]
        
        if keys_to_delete:
            logger.info(f"Invalidating {len(keys_to_delete)} cache key(s).")
            redis_client.delete(*keys_to_delete)


@router.get("/", response_model=List[BookingOut])
def read_bookings(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    room_id: Optional[uuid.UUID] = None,
    on_date: Optional[date] = None,
    future_only: bool = False,
):
    """
    Retrieve bookings.
    - If `room_id` and `on_date` are provided, it returns all bookings for that room on that day (public).
    - If authenticated, it returns the current user's bookings.
    """
    current_user_id = getattr(request.state, "user_id", None)
    logger.info(f"GET bookings (user={'authenticated' if current_user_id else 'guest'}, room_id={room_id}, on_date={on_date})")

    if room_id and on_date:
        # Publicly accessible for timeline view
        bookings = crud.booking.get_multi_by_room_and_date(
            db, room_id=room_id, on_date=on_date
        )
    elif current_user_id:
        # Authenticated user fetching their own bookings
        user_uuid = uuid.UUID(current_user_id)
        bookings = crud.booking.get_multi_by_user(
            db, user_id=user_uuid, future_only=future_only, skip=skip, limit=limit
        )
    else:
        # Unauthenticated user trying to get a list of all bookings.
        # Return empty list to prevent data leakage.
        # A real-world app would have admin role checks here.
        bookings = []

    logger.info(f"GET success - {len(bookings)} bookings")
    return bookings

@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new booking.
    """
    logger.info(f"POST booking for room: {booking.room_id} by user: {current_user}")
    
    # Set the user_id from the authenticated user token, not the request body.
    booking.user_id = uuid.UUID(current_user)

    db_booking = crud.booking.create_with_overlap_check(db=db, obj_in=booking)
    logger.info(f"POST success - created booking with ID: {db_booking.id}")

    # Invalidate the cache for the user's booking list
    _invalidate_user_bookings_cache(current_user)
    return db_booking

@router.get("/{booking_id}", response_model=BookingOut)
def read_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve a single booking by its ID.
    """
    logger.info(f"GET single booking with ID: {booking_id}")
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        logger.warning(f"GET warn - {booking_id} not found")
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Security check: ensure user can only see their own bookings
    if str(db_booking.user_id) != current_user:
        logger.warning(f"GET warn - user {current_user} trying to access booking {booking_id} of user {db_booking.user_id}")
        raise HTTPException(status_code=404, detail="Booking not found")
    return db_booking

@router.put("/{booking_id}", response_model=BookingOut)
def update_booking(
    booking_id: uuid.UUID,
    booking: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing booking.
    """
    logger.info(f"PUT update booking {booking_id}")
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        logger.warning(f"PUT warn - {booking_id} not found for update")
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Security check: ensure user can only update their own bookings
    if str(db_booking.user_id) != current_user:
        logger.warning(f"PUT warn - user {current_user} trying to update booking {booking_id} of user {db_booking.user_id}")
        raise HTTPException(status_code=404, detail="Booking not found")

    db_booking = crud.booking.update(db=db, db_obj=db_booking, obj_in=booking)
    logger.info(f"PUT success - updated booking {booking_id}")

    # Invalidate the cache for the user's booking list
    _invalidate_user_bookings_cache(current_user)
    return db_booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Soft delete a booking (sets is_deleted to True and status to 'cancelled').
    """
    logger.info(f"DELETE soft deleting booking {booking_id}")
    db_booking = crud.booking.get(db, id=booking_id)
    if db_booking is None:
        logger.warning(f"DELETE warn - {booking_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Security check: ensure user can only delete their own bookings
    if str(db_booking.user_id) != current_user:
        logger.warning(f"DELETE warn - user {current_user} trying to delete booking {booking_id} of user {db_booking.user_id}")
        raise HTTPException(status_code=404, detail="Booking not found")

    if db_booking.is_deleted:
        logger.warning(f"DELETE warn - {booking_id} is already deleted")
        raise HTTPException(status_code=404, detail="Booking not found")

    crud.booking.soft_remove_with_status(db=db, db_obj=db_booking)
    logger.info(f"DELETE success - deleted booking {booking_id}")

    # Invalidate the cache for the user's booking list
    _invalidate_user_bookings_cache(current_user)
    
    return None