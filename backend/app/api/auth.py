from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    LoginRequest, TokenResponse, RefreshTokenRequest,
    ChangePasswordRequest, TelegramLinkRequest, TelegramLinkResponse
)
from app.schemas.user import UserResponse, CurrentUser
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens"""
    auth_service = AuthService(db)
    result = await auth_service.authenticate(request.username, request.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    result = await auth_service.refresh_tokens(request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return result


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout current user (invalidate tokens)"""
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    permissions = _get_permissions_for_role(current_user.role)
    
    return CurrentUser(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        telegram_user_id=current_user.telegram_user_id,
        is_superuser=current_user.is_superuser,
        permissions=permissions
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password"""
    auth_service = AuthService(db)
    success = await auth_service.change_password(
        current_user.id,
        request.current_password,
        request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/telegram/link", response_model=TelegramLinkResponse)
async def link_telegram(
    request: TelegramLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Link Telegram account to user"""
    auth_service = AuthService(db)
    result = await auth_service.link_telegram(
        current_user.id,
        request.telegram_user_id,
        request.verification_code
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return TelegramLinkResponse(**result)


@router.post("/telegram/unlink")
async def unlink_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlink Telegram account from user"""
    auth_service = AuthService(db)
    await auth_service.unlink_telegram(current_user.id)
    return {"message": "Telegram account unlinked successfully"}


def _get_permissions_for_role(role) -> list[str]:
    """Get list of permissions for a role"""
    from app.models.user import UserRole
    
    permissions = {
        UserRole.ADMIN: [
            "users.read", "users.write", "users.delete",
            "sources.read", "sources.write", "sources.delete",
            "articles.read", "articles.write", "articles.moderate",
            "rules.read", "rules.write", "rules.delete",
            "templates.read", "templates.write", "templates.delete",
            "targets.read", "targets.write", "targets.delete",
            "analytics.read", "audit.read", "settings.write"
        ],
        UserRole.CHIEF_EDITOR: [
            "sources.read",
            "articles.read", "articles.write", "articles.moderate", "articles.final_approve",
            "rules.read", "rules.write",
            "templates.read", "templates.write",
            "targets.read",
            "analytics.read", "audit.read"
        ],
        UserRole.EDITOR: [
            "sources.read",
            "articles.read", "articles.write", "articles.moderate",
            "rules.read",
            "templates.read",
            "targets.read",
            "analytics.read"
        ],
        UserRole.ANALYST: [
            "sources.read",
            "articles.read",
            "analytics.read", "audit.read"
        ],
        UserRole.SERVICE: [
            "articles.read", "articles.write",
            "sources.read"
        ]
    }
    
    return permissions.get(role, [])
