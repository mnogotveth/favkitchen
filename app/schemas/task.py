from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    deal_id: int
    title: str
    description: Optional[str] = None
    due_date: date = Field(description="Due date in YYYY-MM-DD format")


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    is_done: Optional[bool] = None


class TaskRead(BaseModel):
    id: int
    deal_id: int
    title: str
    description: Optional[str]
    due_date: datetime
    is_done: bool
    created_at: datetime

    class Config:
        from_attributes = True
