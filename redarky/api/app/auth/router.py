from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.auth.service import login_user, register_user
from app.database import get_db
from app.security import create_token, decode_token
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=TokenPair)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await register_user(db, payload)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await login_user(db, payload)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest) -> TokenPair:
    token_payload = decode_token(payload.refresh_token, "refresh")
    user_id = token_payload["sub"]
    return TokenPair(
        access_token=create_token(user_id, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_token=create_token(user_id, "refresh", settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
