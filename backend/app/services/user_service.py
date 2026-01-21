from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import AuthService


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db)
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        query = select(User).where(User.telegram_user_id == telegram_user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_users(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """List users with filters"""
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        # Count total
        count_query = select(func.count(User.id))
        if role:
            count_query = count_query.where(User.role == role)
        if is_active is not None:
            count_query = count_query.where(User.is_active == is_active)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get users
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def create_user(self, data: UserCreate) -> User:
        """Create new user"""
        user = User(
            email=data.email,
            username=data.username,
            password_hash=self.auth_service.hash_password(data.password),
            role=data.role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user(self, user_id: UUID, data: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Deactivate user (soft delete)"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        return True
