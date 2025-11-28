from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import OrganizationContext, get_current_member
from app.db.session import get_session
from app.schemas.analytics import DealsFunnelResponse, DealsSummaryResponse
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/deals/summary", response_model=DealsSummaryResponse)
async def deals_summary(
    days: int = Query(30, ge=1, le=180),
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = AnalyticsService(session)
    return await service.deals_summary(context.organization.id, days=days)


@router.get("/deals/funnel", response_model=DealsFunnelResponse)
async def deals_funnel(
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = AnalyticsService(session)
    return await service.deals_funnel(context.organization.id)
