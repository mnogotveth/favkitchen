from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActivityType
from app.models.models import Activity
from app.repositories.activity_repository import ActivityRepository
from app.repositories.deal_repository import DealRepository
from app.schemas.activity import ActivityCreate


class ActivityService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.activities = ActivityRepository(session)
        self.deals = DealRepository(session)

    async def list_for_deal(self, organization_id: int, deal_id: int) -> list[Activity]:
        deal = await self.deals.get(organization_id, deal_id)
        if not deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        return await self.activities.list_for_deal(deal.id)

    async def add_comment(
        self, organization_id: int, deal_id: int, *, author_id: int, data: ActivityCreate
    ) -> Activity:
        if data.type != ActivityType.COMMENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Manual activities must be comments"
            )
        deal = await self.deals.get(organization_id, deal_id)
        if not deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        activity = Activity(
            deal_id=deal.id,
            author_id=author_id,
            type=ActivityType.COMMENT,
            payload=data.payload,
        )
        await self.activities.create(activity)
        await self.session.commit()
        return activity
