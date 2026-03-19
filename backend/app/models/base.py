# backend/app/models/base.py
from sqlalchemy import Column, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
import uuid

from ..core.database import Base

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None