from __future__ import annotations

from sqlalchemy import select

from app.models.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return await self.session.scalar(stmt)

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
