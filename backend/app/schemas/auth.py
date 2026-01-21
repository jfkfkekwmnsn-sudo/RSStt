from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID

from app.models.user import UserRole


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int
    type: str  # access or refresh


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class TelegramLinkRequest(BaseModel):
    telegram_user_id: int
    verification_code: str


class TelegramLinkResponse(BaseModel):
    success: bool
    message: str
    telegram_username: Optional[str] = None
