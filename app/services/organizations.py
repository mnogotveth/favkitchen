from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.repo = OrganizationRepository(session)

    async def list_for_user(self, user_id: int):
        return await self.repo.list_for_user(user_id)
