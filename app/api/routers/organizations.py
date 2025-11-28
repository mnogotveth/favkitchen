from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_session
from app.schemas.organization import OrganizationMembershipRead, OrganizationRead
from app.schemas.user import UserRead
from app.services.organizations import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=list[OrganizationMembershipRead])
async def me(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    service = OrganizationService(session)
    rows = await service.list_for_user(current_user.id)
    response: list[OrganizationMembershipRead] = []
    for organization, membership in rows:
        response.append(
            OrganizationMembershipRead(
                organization=OrganizationRead.model_validate(organization),
                role=membership.role,
            )
        )
    return response
