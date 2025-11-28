from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel

from app.models.enums import DealStage, DealStatus


class DealsSummaryResponse(BaseModel):
    count_by_status: Dict[DealStatus, int]
    amount_by_status: Dict[DealStatus, Decimal]
    average_won_amount: Optional[Decimal]
    new_deals_last_n_days: int


class DealFunnelStageBreakdown(BaseModel):
    stage: DealStage
    counts: Dict[DealStatus, int]
    conversion_from_previous: Optional[float]


class DealsFunnelResponse(BaseModel):
    stages: list[DealFunnelStageBreakdown]
