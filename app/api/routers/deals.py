from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import OrganizationContext, get_current_member
from app.core.config import get_settings
from app.db.session import get_session
from app.models.enums import DealStage, DealStatus
from app.schemas.deal import DealCreate, DealRead, DealUpdate
from app.services.deals import DealService

settings = get_settings()

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=list[DealRead])
async def list_deals(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    status: list[DealStatus] = Query(default=[]),
    min_amount: Decimal | None = Query(default=None, ge=0),
    max_amount: Decimal | None = Query(default=None, ge=0),
    stage: DealStage | None = None,
    owner_id: int | None = Query(default=None, description="Filter by owner (admins only)"),
    order_by: str = Query("created_at"),
    order: str = Query("desc", pattern="^(?i)(asc|desc)$"),
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = DealService(session)
    deals = await service.list_deals(
        context.organization.id,
        role=context.membership.role,
        page=page,
        page_size=page_size,
        statuses=status or None,
        min_amount=min_amount,
        max_amount=max_amount,
        stage=stage,
        owner_id=owner_id,
        order_by=order_by,
        order=order,
    )
    return [DealRead.model_validate(deal) for deal in deals]


@router.post("", response_model=DealRead, status_code=201)
async def create_deal(
    payload: DealCreate,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = DealService(session)
    deal = await service.create_deal(
        context.organization.id,
        role=context.membership.role,
        requestor_id=context.membership.user_id,
        data=payload,
    )
    return DealRead.model_validate(deal)


@router.patch("/{deal_id}", response_model=DealRead)
async def update_deal(
    deal_id: int,
    payload: DealUpdate,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = DealService(session)
    deal = await service.update_deal(
        context.organization.id,
        user_id=context.membership.user_id,
        role=context.membership.role,
        deal_id=deal_id,
        data=payload,
    )
    return DealRead.model_validate(deal)
