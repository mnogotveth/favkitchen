from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MemberRole
from app.models.models import Contact, OrganizationMember
from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactCreate


class ContactService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ContactRepository(session)

    async def list_contacts(
        self,
        organization_id: int,
        *,
        role: MemberRole,
        page: int,
        page_size: int,
        search: str | None,
        owner_id: int | None,
    ) -> list[Contact]:
        owner_filter = owner_id if role != MemberRole.MEMBER else None
        return await self.repo.list(
            organization_id,
            page=page,
            page_size=page_size,
            search=search,
            owner_id=owner_filter,
        )

    async def create_contact(
        self,
        organization_id: int,
        *,
        role: MemberRole,
        requestor_id: int,
        data: ContactCreate,
    ) -> Contact:
        if role != MemberRole.MEMBER and data.owner_id:
            await self._ensure_member(organization_id, data.owner_id)
            owner_id = data.owner_id
        else:
            owner_id = requestor_id
        contact = Contact(
            organization_id=organization_id,
            owner_id=owner_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
        )
        await self.repo.create(contact)
        await self.session.commit()
        return contact

    async def delete_contact(
        self,
        organization_id: int,
        contact_id: int,
        *,
        role: MemberRole,
        requestor_id: int,
    ) -> None:
        contact = await self.repo.get(organization_id, contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        if role == MemberRole.MEMBER and contact.owner_id != requestor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        if await self.repo.has_deals(contact.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact has deals and cannot be removed",
            )
        await self.repo.delete(contact)
        await self.session.commit()

    async def _ensure_member(self, organization_id: int, user_id: int) -> None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        member = await self.session.scalar(stmt)
        if not member:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown owner")
