from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import OrganizationContext, get_current_member
from app.db.session import get_session
from app.schemas.activity import ActivityCreate, ActivityRead
from app.services.activities import ActivityService

router = APIRouter(prefix="/deals/{deal_id}/activities", tags=["activities"])


@router.get("", response_model=list[ActivityRead])
async def list_activities(
    deal_id: int,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = ActivityService(session)
    activities = await service.list_for_deal(context.organization.id, deal_id)
    return [ActivityRead.model_validate(item) for item in activities]


@router.post("", response_model=ActivityRead, status_code=201)
async def create_comment(
    deal_id: int,
    payload: ActivityCreate,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = ActivityService(session)
    activity = await service.add_comment(
        context.organization.id,
        deal_id,
        author_id=context.membership.user_id,
        data=payload,
    )
    return ActivityRead.model_validate(activity)
