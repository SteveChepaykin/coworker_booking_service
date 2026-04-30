from sqlalchemy.orm import Session
from typing import List

from .base import CRUDBase
from ..models.coworking_space import CoworkingSpace

class CRUDSpace(CRUDBase[CoworkingSpace, None, None]):
    def get_multi_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[CoworkingSpace]:
        return (
            db.query(self.model)
            .filter(self.model.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

space = CRUDSpace(CoworkingSpace)