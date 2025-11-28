from __future__ import annotations

from fastapi import APIRouter, Depends

from app.db.session import get_session
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair)
async def register(payload: RegisterRequest, session=Depends(get_session)):
    service = AuthService(session)
    return await service.register(payload)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, session=Depends(get_session)):
    service = AuthService(session)
    return await service.login(payload)
