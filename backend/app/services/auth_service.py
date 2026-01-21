from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.auth import TokenResponse
from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.secret_key = settings.SECRET_KEY
        self.jwt_secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def authenticate(self, username: str, password: str) -> Optional[TokenResponse]:
        """Authenticate user by username and password"""
        try:
            query = select(User).where(
                (User.username == username) | (User.email == username)
            )
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return None

            if not self.verify_password(password, user.hashed_password):
                return None

            if not user.is_active:
                return None

            access_token = self.create_access_token(
                data={"sub": str(user.id), "type": "access"}
            )
            refresh_token = self.create_refresh_token(
                data={"sub": str(user.id)}
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def refresh_tokens(self, refresh_token: str) -> Optional[TokenResponse]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                self.jwt_secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            query = select(User).where(User.id == UUID(user_id))
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return None

            access_token = self.create_access_token(
                data={"sub": user_id, "type": "access"}
            )
            new_refresh_token = self.create_refresh_token(
                data={"sub": user_id}
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60
            )
        except JWTError:
            return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None

    async def logout(self, user_id: UUID) -> bool:
        """Logout user (invalidate tokens)"""
        try:
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return False

            if not self.verify_password(current_password, user.hashed_password):
                return False

            user.hashed_password = self.get_password_hash(new_password)
            self.db.add(user)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Change password error: {e}")
            await self.db.rollback()
            return False

    async def link_telegram(
        self, user_id: UUID, telegram_user_id: int, verification_code: str
    ) -> Dict[str, Any]:
        """Link Telegram account to user"""
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return {"success": False, "message": "User not found"}

            if not verification_code:
                return {"success": False, "message": "Invalid verification code"}

            existing_query = select(User).where(
                (User.telegram_user_id == telegram_user_id) & (User.id != user_id)
            )
            existing_result = await self.db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                return {"success": False, "message": "Telegram account already linked to another user"}

            user.telegram_user_id = telegram_user_id
            self.db.add(user)
            await self.db.commit()

            return {
                "success": True,
                "message": "Telegram account linked successfully",
                "telegram_user_id": telegram_user_id
            }
        except Exception as e:
            logger.error(f"Link telegram error: {e}")
            await self.db.rollback()
            return {"success": False, "message": str(e)}

    async def unlink_telegram(self, user_id: UUID) -> bool:
        """Unlink Telegram account from user"""
        try:
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return False

            user.telegram_user_id = None
            self.db.add(user)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Unlink telegram error: {e}")
            await self.db.rollback()
            return False

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError:
            return None
