from pydantic import BaseModel, EmailStr
import uuid
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True