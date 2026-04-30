from datetime import datetime
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .base import CRUDBase
from ..models.booking import Booking
from ..models.room import Room
from ..schemas.booking import BookingCreate, BookingUpdate

class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    def get_multi_by_user(
        self, db: Session, *, user_id: uuid.UUID, future_only: bool = False, skip: int = 0, limit: int = 100
    ) -> List[Booking]:
        query = db.query(self.model).filter(Booking.user_id == user_id)
        if future_only:
            query = query.filter(Booking.start_time > datetime.utcnow())
        return query.order_by(Booking.start_time.asc()).offset(skip).limit(limit).all()

    def create_with_overlap_check(self, db: Session, *, obj_in: BookingCreate) -> Booking:
        # Check if room is active
        room = db.query(Room).filter(Room.id == obj_in.room_id, Room.is_active == True).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active room not found")

        # This check is a safeguard. The primary guard against overlaps is the
        # EXCLUDE constraint in the PostgreSQL database. This provides a friendlier
        # HTTP error before the database raises a generic IntegrityError.
        overlapping_booking = db.query(Booking).filter(
            Booking.room_id == obj_in.room_id,
            Booking.end_time > obj_in.start_time,
            Booking.start_time < obj_in.end_time,
            Booking.status == 'confirmed',
            Booking.is_deleted == False
        ).first()

        if overlapping_booking:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking conflict: The room is already booked for the requested time.")

        return super().create(db, obj_in=obj_in)

    def soft_remove_with_status(self, db: Session, *, db_obj: Booking) -> Booking:
        db_obj.status = "cancelled"
        return super().soft_remove(db, db_obj=db_obj)

booking = CRUDBooking(Booking)