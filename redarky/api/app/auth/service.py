from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RegisterRequest, TokenPair
from app.config import settings
from app.models import User
from app.security import create_token, hash_password, verify_password


def _issue_token_pair(user_id: str) -> TokenPair:
    return TokenPair(
        access_token=create_token(user_id, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_token=create_token(user_id, "refresh", settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )


async def register_user(db: AsyncSession, payload: RegisterRequest) -> TokenPair:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _issue_token_pair(str(user.id))


async def login_user(db: AsyncSession, payload: LoginRequest) -> TokenPair:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _issue_token_pair(str(user.id))
