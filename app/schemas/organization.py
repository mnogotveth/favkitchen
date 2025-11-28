from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import MemberRole


class OrganizationRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationMembershipRead(BaseModel):
    organization: OrganizationRead
    role: MemberRole
