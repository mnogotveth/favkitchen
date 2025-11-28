from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActivityType, DealStage, DealStatus, MemberRole
from app.models.models import Activity, Contact, Deal, OrganizationMember
from app.repositories.deal_repository import DealRepository
from app.schemas.deal import DealCreate, DealUpdate

STAGE_ORDER = {
    DealStage.QUALIFICATION: 1,
    DealStage.PROPOSAL: 2,
    DealStage.NEGOTIATION: 3,
    DealStage.CLOSED: 4,
}


class DealService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DealRepository(session)

    async def list_deals(
        self,
        organization_id: int,
        *,
        role: MemberRole,
        page: int,
        page_size: int,
        statuses: list[DealStatus] | None,
        min_amount: Decimal | None,
        max_amount: Decimal | None,
        stage: DealStage | None,
        owner_id: int | None,
        order_by: str,
        order: str,
    ) -> list[Deal]:
        effective_owner = owner_id if role != MemberRole.MEMBER else None
        return await self.repo.list(
            organization_id,
            page=page,
            page_size=page_size,
            statuses=statuses,
            min_amount=min_amount,
            max_amount=max_amount,
            stage=stage,
            owner_id=effective_owner,
            order_by=order_by,
            order=order,
        )

    async def create_deal(
        self,
        organization_id: int,
        *,
        role: MemberRole,
        requestor_id: int,
        data: DealCreate,
    ) -> Deal:
        if role != MemberRole.MEMBER and data.owner_id:
            await self._ensure_member(organization_id, data.owner_id)
            owner_id = data.owner_id
        else:
            owner_id = requestor_id
        contact = await self._get_contact_in_org(organization_id, data.contact_id)
        deal = Deal(
            organization_id=organization_id,
            contact_id=contact.id,
            owner_id=owner_id,
            title=data.title,
            amount=data.amount,
            currency=data.currency,
        )
        await self.repo.create(deal)
        await self.session.commit()
        return deal

    async def update_deal(
        self,
        organization_id: int,
        *,
        user_id: int,
        role: MemberRole,
        deal_id: int,
        data: DealUpdate,
    ) -> Deal:
        deal = await self.repo.get(organization_id, deal_id)
        if not deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        if role == MemberRole.MEMBER and deal.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

        previous_status = deal.status
        previous_stage = deal.stage

        if data.title is not None:
            deal.title = data.title
        if data.amount is not None:
            deal.amount = data.amount
        if data.currency is not None:
            deal.currency = data.currency
        if data.owner_id is not None:
            if role == MemberRole.MEMBER:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
            await self._ensure_member(organization_id, data.owner_id)
            deal.owner_id = data.owner_id
        if data.stage is not None:
            self._validate_stage_transition(previous_stage, data.stage, role)
            deal.stage = data.stage
        if data.status is not None:
            if data.status == DealStatus.WON and (deal.amount is None or deal.amount <= 0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Won deal must have amount"
                )
            deal.status = data.status

        await self.session.flush()
        await self._record_activity_if_needed(deal, previous_status, previous_stage)
        await self.session.commit()
        return deal

    async def _record_activity_if_needed(
        self, deal: Deal, previous_status: DealStatus, previous_stage: DealStage
    ) -> None:
        activities: list[Activity] = []
        if deal.status != previous_status:
            activities.append(
                Activity(
                    deal_id=deal.id,
                    type=ActivityType.STATUS_CHANGED,
                    payload={"from": previous_status.value, "to": deal.status.value},
                )
            )
        if deal.stage != previous_stage:
            activities.append(
                Activity(
                    deal_id=deal.id,
                    type=ActivityType.STAGE_CHANGED,
                    payload={"from": previous_stage.value, "to": deal.stage.value},
                )
            )
        if activities:
            self.session.add_all(activities)

    def _validate_stage_transition(
        self, current_stage: DealStage, new_stage: DealStage, role: MemberRole
    ) -> None:
        if role in {MemberRole.ADMIN, MemberRole.OWNER}:
            return
        if STAGE_ORDER[new_stage] < STAGE_ORDER[current_stage]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot move stage backwards"
            )

    async def _get_contact_in_org(self, organization_id: int, contact_id: int) -> Contact:
        stmt = select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == organization_id,
        )
        contact = await self.session.scalar(stmt)
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contact not in organization"
            )
        return contact

    async def _ensure_member(self, organization_id: int, user_id: int) -> None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        if not await self.session.scalar(stmt):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown owner")
