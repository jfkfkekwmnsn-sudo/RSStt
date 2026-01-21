from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    role: UserRole = UserRole.EDITOR


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    telegram_username: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CurrentUser(BaseModel):
    id: UUID
    username: str
    email: str
    role: UserRole
    telegram_user_id: Optional[int] = None
    is_superuser: bool
    permissions: list[str] = []

    class Config:
        from_attributes = True
