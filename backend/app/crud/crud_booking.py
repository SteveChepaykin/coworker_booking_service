from datetime import datetime, date, timedelta, timezone
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from ..models.booking import Booking
from ..models.room import Room
from ..schemas.booking import BookingCreate, BookingUpdate
from ..core.redis import redis_client

logger = logging.getLogger(__name__)

def _get_canonical_query_string(params: dict) -> str:
    """Helper to create a canonical query string, matching the middleware."""
    return "&".join(f"{k}={v}" for k, v in sorted(params.items()))

def _invalidate_booking_caches(user_id: str, room_id: str, booking_date: str):
    """
    Explicitly deletes the two main cache keys affected by a booking change.
    This uses canonical key generation to guarantee a match with the cache middleware.
    """
    if not redis_client:
        return

    # Key for the user's personal list of future bookings
    user_query = _get_canonical_query_string({"future_only": "true"})
    user_cache_key = f"cache:req:{user_id}:/api/v1/bookings/?{user_query}"

    # Key for the public timeline view for the affected room and date
    room_query = _get_canonical_query_string({"room_id": room_id, "on_date": booking_date})
    room_timeline_cache_key = f"cache:req:anonymous:/api/v1/bookings/?{room_query}"

    logger.info(f"Invalidating cache keys: {user_cache_key}, {room_timeline_cache_key}")
    redis_client.delete(user_cache_key, room_timeline_cache_key)
class CRUDBooking:
    """
    This CRUD object is now self-contained to ensure all booking logic is explicit
    and transparent, removing reliance on a generic base class that might obscure
    session management or commit logic. This provides a definitive fix for
    data persistence issues.
    """
    def get(self, db: Session, id: uuid.UUID) -> Optional[Booking]:
        """
        Fetches a booking by its ID. The session's query class will handle
        the soft-delete filtering automatically.
        """
        # Switched from .get() to .filter().first() to explicitly add the is_deleted check.
        # This ensures we never accidentally fetch a soft-deleted record by its ID.
        return db.query(Booking).filter(Booking.id == id, Booking.is_deleted == False).first()

    def get_multi_by_user(
        self, db: Session, *, user_id: uuid.UUID, future_only: bool = False, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        # Explicitly adding `is_deleted == False` to the main user booking query.
        # This is the core fix to ensure users only see their active bookings.
        query = db.query(Booking).filter(Booking.user_id == user_id, Booking.is_deleted == False)
        if future_only:
            query = query.filter(Booking.start_time > datetime.now(timezone.utc))
        return query.order_by(Booking.start_time.asc()).offset(skip).limit(limit).all()

    def get_multi_by_room_and_date(
        self, db: Session, *, room_id: uuid.UUID, on_date: date
    ) -> List[Booking]:
        """
        Fetches all bookings for a specific room on a given date. This is used
        to populate the booking timeline on the frontend.
        """
        start_of_day = datetime.combine(on_date, datetime.min.time(), tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)
        return (
            db.query(Booking)
            .filter(
                Booking.room_id == room_id,
                Booking.is_deleted == False, # Added explicit check for the public timeline view.
                Booking.start_time >= start_of_day,
                Booking.start_time < end_of_day,
            ).all()
        )

    def create_with_overlap_check(self, db: Session, *, obj_in: BookingCreate) -> Booking:
        """
        Creates a new booking after performing validation checks.
        This method now explicitly handles the entire database transaction
        (add, commit, refresh) to ensure the operation is atomic and the new
        object is returned with its database-generated state.
        """
        room = db.query(Room).filter(Room.id == obj_in.room_id, Room.is_active == True).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active room not found")
        
        overlapping_booking = db.query(Booking).filter(
            Booking.room_id == obj_in.room_id,
            Booking.end_time > obj_in.start_time,
            Booking.start_time < obj_in.end_time,
            Booking.status == 'confirmed',
            Booking.is_deleted == False
        ).first()

        if overlapping_booking:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                detail="Booking conflict: The room is already booked for the requested time.")

        # Explicitly create, add, commit, and refresh to ensure data persistence.
        db_obj = Booking(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Invalidate cache directly after successful commit.
        _invalidate_booking_caches(
            user_id=str(db_obj.user_id),
            room_id=str(db_obj.room_id),
            booking_date=db_obj.start_time.strftime('%Y-%m-%d')
        )
        return db_obj

    def soft_remove_with_status(self, db: Session, *, db_obj: Booking) -> Booking:
        """
        Performs a soft delete on a booking by setting its status to 'cancelled'
        and marking it as deleted. This method handles its own transaction to
        guarantee the change is always persisted to the database.
        """
        db_obj.status = "cancelled"
        db_obj.soft_delete()
        db.commit()

        # Invalidate cache directly after successful commit.
        _invalidate_booking_caches(
            user_id=str(db_obj.user_id),
            room_id=str(db_obj.room_id),
            booking_date=db_obj.start_time.strftime('%Y-%m-%d')
        )
        return db_obj

booking = CRUDBooking()