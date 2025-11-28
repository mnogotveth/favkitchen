from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Select, func, select

from app.models.enums import DealStage, DealStatus
from app.models.models import Deal
from app.repositories.base import BaseRepository

OrderFields = {
    "created_at": Deal.created_at,
    "amount": Deal.amount,
    "updated_at": Deal.updated_at,
    "title": Deal.title,
}


class DealRepository(BaseRepository):
    def _base_query(self, organization_id: int) -> Select[tuple[Deal]]:
        return select(Deal).where(Deal.organization_id == organization_id)

    async def list(
        self,
        organization_id: int,
        *,
        page: int,
        page_size: int,
        statuses: list[DealStatus] | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        stage: DealStage | None = None,
        owner_id: int | None = None,
        order_by: str = "created_at",
        order: str = "desc",
    ) -> list[Deal]:
        stmt = self._base_query(organization_id)
        if statuses:
            stmt = stmt.where(Deal.status.in_(statuses))
        if min_amount is not None:
            stmt = stmt.where(Deal.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(Deal.amount <= max_amount)
        if stage:
            stmt = stmt.where(Deal.stage == stage)
        if owner_id is not None:
            stmt = stmt.where(Deal.owner_id == owner_id)
        order_column = OrderFields.get(order_by, Deal.created_at)
        order_clause = order_column.desc() if order.lower() == "desc" else order_column.asc()
        stmt = stmt.order_by(order_clause).offset((page - 1) * page_size).limit(page_size)
        rows = await self.session.scalars(stmt)
        return list(rows.all())

    async def create(self, deal: Deal) -> Deal:
        self.session.add(deal)
        await self.session.flush()
        return deal

    async def get(self, organization_id: int, deal_id: int) -> Deal | None:
        stmt = self._base_query(organization_id).where(Deal.id == deal_id)
        return await self.session.scalar(stmt)

    async def summarise_by_status(
        self, organization_id: int
    ) -> list[tuple[DealStatus, int, Decimal]]:
        stmt = (
            select(Deal.status, func.count(Deal.id), func.coalesce(func.sum(Deal.amount), 0))
            .where(Deal.organization_id == organization_id)
            .group_by(Deal.status)
        )
        rows = await self.session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in rows.all()]

    async def average_won_amount(self, organization_id: int) -> Decimal | None:
        stmt = select(func.avg(Deal.amount)).where(
            Deal.organization_id == organization_id, Deal.status == DealStatus.WON
        )
        return await self.session.scalar(stmt)

    async def count_new_deals(self, organization_id: int, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(func.count(Deal.id)).where(
            Deal.organization_id == organization_id, Deal.created_at >= cutoff
        )
        value = await self.session.scalar(stmt)
        return int(value or 0)

    async def funnel_counts(self, organization_id: int) -> list[tuple[DealStage, DealStatus, int]]:
        stmt = (
            select(Deal.stage, Deal.status, func.count(Deal.id))
            .where(Deal.organization_id == organization_id)
            .group_by(Deal.stage, Deal.status)
        )
        rows = await self.session.execute(stmt)
        return [(row[0], row[1], row[2]) for row in rows.all()]
