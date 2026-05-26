from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..core.security import verify_password, get_password_hash
from ..models.user import User
from ..schemas.user import UserCreate


def get_user_by_username(db: Session, *, username: str) -> Optional[User]:
    """Retrieve a user by their username."""
    return db.query(User).filter(User.username == username, User.is_deleted == False).first()


def get_user_by_email(db: Session, *, email: str) -> Optional[User]:
    """Retrieve a user by their email."""
    return db.query(User).filter(User.email == email, User.is_deleted == False).first()


def create(db: Session, *, obj_in: UserCreate) -> User:
    """Create a new user."""
    if get_user_by_username(db, username=obj_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists.",
        )
    if get_user_by_email(db, email=obj_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    create_data = obj_in.model_dump(exclude={"password"})
    hashed_password = get_password_hash(obj_in.password)
    db_obj = User(**create_data, hashed_password=hashed_password)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def authenticate(db: Session, *, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password."""
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user