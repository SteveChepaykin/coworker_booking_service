# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Query, Session
from sqlalchemy.sql import expression
import logging

from .config import settings

logger = logging.getLogger(__name__)

class SoftDeleteQuery(Query):
    """Query class that automatically filters out soft-deleted records"""

    def __iter__(self):
        if self._execution_options.get("include_deleted", False):
            return super().__iter__()

        entity = self._entity_zero()
        if hasattr(entity.class_, 'is_deleted'):
            return super().filter(entity.class_.is_deleted == False).__iter__()

        return super().__iter__()

    def with_deleted(self):
        """Include soft-deleted records in query"""
        return self.execution_options(include_deleted=True)

    def only_deleted(self):
        """Return only soft-deleted records"""
        entity = self._entity_zero()
        if hasattr(entity.class_, 'is_deleted'):
            return self.with_deleted().filter(entity.class_.is_deleted == True)
        return self

class Base(declarative_base()):
    __abstract__ = True
    query_class = SoftDeleteQuery

engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0,
    echo=settings.DEBUG,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, query_cls=SoftDeleteQuery)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()