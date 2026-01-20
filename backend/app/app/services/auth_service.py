from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction
from app.utils.redis import get_redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def create_access_token(self, user_id: UUID) -> tuple[str, int]:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access"
        }
        
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return token, int(expires_delta.total_seconds())
    
    def create_refresh_token(self, user_id: UUID) -> str:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    async def authenticate(self, username: str, password: str) -> Optional[TokenResponse]:
        query = select(User).where(
            (User.username == username) | (User.email == username)
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not self.verify_password(password, user.password_hash):
            return None
        
        if not user.is_active:
            return None
        
        access_token, expires_in = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)
        
        # Log login
        await self.audit.log(
            action=AuditAction.USER_LOGIN,
            entity_type="user",
            entity_id=user.id,
            actor_id=user.id,
            actor_type="user"
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[TokenResponse]:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            if payload.get("type") != "refresh":
                return None
            
            user_id = UUID(payload.get("sub"))
            
            # Check if token is blacklisted
            redis = await get_redis()
            if await redis.get(f"token_blacklist:{refresh_token}"):
                return None
            
            # Get user
            query = select(User).where(User.id == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                return None
            
            # Create new tokens
            access_token, expires_in = self.create_access_token(user.id)
            new_refresh_token = self.create_refresh_token(user.id)
            
            # Blacklist old refresh token
            await redis.setex(
                f"token_blacklist:{refresh_token}",
                settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                "1"
            )
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=expires_in
            )
            
        except Exception:
            return None
    
    async def logout(self, user_id: UUID):
        """Logout user - invalidate all tokens"""
        await self.audit.log(
            action=AuditAction.USER_LOGOUT,
            entity_type="user",
            entity_id=user_id,
            actor_id=user_id,
            actor_type="user"
        )
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> bool:
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        if not self.verify_password(current_password, user.password_hash):
            return False
        
        user.password_hash = self.hash_password(new_password)
        await self.db.commit()
        
        return True
    
    async def link_telegram(
        self,
        user_id: UUID,
        telegram_user_id: int,
        verification_code: str
    ) -> dict:
        # Verify code from Redis
        redis = await get_redis()
        stored_code = await redis.get(f"telegram_link:{user_id}")
        
        if not stored_code or stored_code.decode() != verification_code:
            return {"success": False, "message": "Invalid or expired verification code"}
        
        # Check if telegram_user_id already linked
        query = select(User).where(User.telegram_user_id == telegram_user_id)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing and existing.id != user_id:
            return {"success": False, "message": "Telegram account already linked to another user"}
        
        # Update user
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return {"success": False, "message": "User not found"}
        
        user.telegram_user_id = telegram_user_id
        await self.db.commit()
        
        # Clean up
        await redis.delete(f"telegram_link:{user_id}")
        
        return {
            "success": True,
            "message": "Telegram account linked successfully",
            "telegram_username": user.telegram_username
        }
    
    async def unlink_telegram(self, user_id: UUID):
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.telegram_user_id = None
            user.telegram_username = None
            await self.db.commit()