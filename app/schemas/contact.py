from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    name: str = Field(min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    owner_id: Optional[int] = Field(default=None, description="Owner user id (admins only)")


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class ContactRead(BaseModel):
    id: int
    organization_id: int
    owner_id: int
    name: str
    email: Optional[EmailStr]
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
