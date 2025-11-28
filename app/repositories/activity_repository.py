from __future__ import annotations

from sqlalchemy import select

from app.models.models import Activity
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository):
    async def list_for_deal(self, deal_id: int) -> list[Activity]:
        stmt = select(Activity).where(Activity.deal_id == deal_id).order_by(Activity.created_at.asc())
        rows = await self.session.scalars(stmt)
        return list(rows.all())

    async def create(self, activity: Activity) -> Activity:
        self.session.add(activity)
        await self.session.flush()
        return activity
