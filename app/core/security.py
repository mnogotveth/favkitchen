from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    token_type: str
    exp: datetime


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    payload: Dict[str, Any] = {
        "sub": subject,
        "token_type": token_type,
        "exp": datetime.now(tz=timezone.utc) + expires_delta,
    }
    return jwt.encode(
        payload,
        settings.token.secret_key,
        algorithm=settings.token.algorithm,
    )


def decode_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.token.secret_key,
            algorithms=[settings.token.algorithm],
        )
    except JWTError as exc:  # pragma: no cover - jose already tested
        raise ValueError("Invalid token") from exc
    return TokenPayload(**payload)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
