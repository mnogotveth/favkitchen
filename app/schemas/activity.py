from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.enums import ActivityType


class ActivityCreate(BaseModel):
    type: ActivityType = Field(default=ActivityType.COMMENT)
    payload: Dict[str, Any]


class ActivityRead(BaseModel):
    id: int
    deal_id: int
    author_id: Optional[int]
    type: ActivityType
    payload: Dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True
