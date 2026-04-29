from typing import Optional, List
import uuid
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.room import Room
from ..schemas.room import RoomCreate, RoomUpdate

class CRUDRoom(CRUDBase[Room, RoomCreate, RoomUpdate]):
    def get_multi_by_space(
        self, db: Session, *, coworking_space_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Room]:
        return (
            db.query(self.model)
            .filter(self.model.coworking_space_id == coworking_space_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

room = CRUDRoom(Room)