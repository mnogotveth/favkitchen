from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import DealStage, DealStatus


class DealCreate(BaseModel):
    contact_id: int
    title: str
    amount: Decimal = Field(ge=0)
    currency: str = Field(min_length=1, max_length=8)
    owner_id: Optional[int] = Field(default=None, description="Owner user id (admins only)")


class DealUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = None
    status: Optional[DealStatus] = None
    stage: Optional[DealStage] = None
    owner_id: Optional[int] = None


class DealRead(BaseModel):
    id: int
    organization_id: int
    contact_id: int
    owner_id: int
    title: str
    amount: Decimal
    currency: str
    status: DealStatus
    stage: DealStage
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
