from __future__ import annotations

from decimal import Decimal
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.caching.memory import SimpleTTLCache
from app.core.config import get_settings
from app.models.enums import DealStage, DealStatus
from app.repositories.deal_repository import DealRepository
from app.schemas.analytics import DealFunnelStageBreakdown, DealsFunnelResponse, DealsSummaryResponse


class AnalyticsService:
    _summary_cache: SimpleTTLCache[DealsSummaryResponse] = SimpleTTLCache()
    _funnel_cache: SimpleTTLCache[DealsFunnelResponse] = SimpleTTLCache()

    def __init__(self, session: AsyncSession):
        self.repo = DealRepository(session)
        self.settings = get_settings()

    async def deals_summary(self, organization_id: int, *, days: int) -> DealsSummaryResponse:
        cache_key = (organization_id, days, "summary")
        cached = self._summary_cache.get(cache_key)
        if cached:
            return cached

        rows = await self.repo.summarise_by_status(organization_id)
        count_by_status: Dict[DealStatus, int] = {status: 0 for status in DealStatus}
        amount_by_status: Dict[DealStatus, Decimal] = {status: Decimal("0") for status in DealStatus}
        for status, count, total in rows:
            count_by_status[status] = count
            amount_by_status[status] = total

        average = await self.repo.average_won_amount(organization_id)
        recent = await self.repo.count_new_deals(organization_id, days)

        response = DealsSummaryResponse(
            count_by_status=count_by_status,
            amount_by_status=amount_by_status,
            average_won_amount=average,
            new_deals_last_n_days=recent,
        )
        self._summary_cache.set(cache_key, response, self.settings.analytics_cache_ttl_seconds)
        return response

    async def deals_funnel(self, organization_id: int) -> DealsFunnelResponse:
        cache_key = (organization_id, "funnel")
        cached = self._funnel_cache.get(cache_key)
        if cached:
            return cached

        rows = await self.repo.funnel_counts(organization_id)
        result: dict[DealStage, Dict[DealStatus, int]] = {
            stage: {status: 0 for status in DealStatus} for stage in DealStage
        }
        for stage, status, count in rows:
            result[stage][status] = count

        ordered_stages = list(DealStage)
        previous_total: int | None = None
        breakdown: list[DealFunnelStageBreakdown] = []
        for stage in ordered_stages:
            stage_total = sum(result[stage].values())
            if previous_total in (None, 0):
                conversion = None
            else:
                conversion = (stage_total / previous_total * 100) if previous_total else None
            breakdown.append(
                DealFunnelStageBreakdown(
                    stage=stage,
                    counts=result[stage],
                    conversion_from_previous=round(conversion, 2) if conversion is not None else None,
                )
            )
            previous_total = stage_total if stage_total > 0 else previous_total

        response = DealsFunnelResponse(stages=breakdown)
        self._funnel_cache.set(cache_key, response, self.settings.analytics_cache_ttl_seconds)
        return response
