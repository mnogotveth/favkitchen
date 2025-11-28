from __future__ import annotations

from sqlalchemy import func, select

from app.models.models import Contact, Deal
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository):
    async def list(
        self,
        organization_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        owner_id: int | None = None,
    ) -> list[Contact]:
        stmt = select(Contact).where(Contact.organization_id == organization_id)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                func.lower(Contact.name).like(like) | func.lower(Contact.email).like(like)
            )
        if owner_id is not None:
            stmt = stmt.where(Contact.owner_id == owner_id)
        stmt = stmt.order_by(Contact.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(self, contact: Contact) -> Contact:
        self.session.add(contact)
        await self.session.flush()
        return contact

    async def get(self, organization_id: int, contact_id: int) -> Contact | None:
        stmt = select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == organization_id,
        )
        return await self.session.scalar(stmt)

    async def delete(self, contact: Contact) -> None:
        await self.session.delete(contact)

    async def has_deals(self, contact_id: int) -> bool:
        stmt = select(func.count(Deal.id)).where(Deal.contact_id == contact_id)
        count = await self.session.scalar(stmt)
        return (count or 0) > 0
