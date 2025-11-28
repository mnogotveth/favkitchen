from __future__ import annotations

from sqlalchemy import select

from app.models.enums import MemberRole
from app.models.models import Organization, OrganizationMember
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository):
    async def create(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.flush()
        return organization

    async def add_member(
        self, membership: OrganizationMember, *, role: MemberRole | None = None
    ) -> OrganizationMember:
        if role:
            membership.role = role
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def list_for_user(self, user_id: int) -> list[tuple[Organization, OrganizationMember]]:
        stmt = (
            select(Organization, OrganizationMember)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.created_at)
        )
        rows = await self.session.execute(stmt)
        return list(rows.all())

    async def get_member(self, organization_id: int, user_id: int) -> OrganizationMember | None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        return await self.session.scalar(stmt)
