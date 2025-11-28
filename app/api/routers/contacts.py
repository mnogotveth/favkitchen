from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import OrganizationContext, get_current_member
from app.core.config import get_settings
from app.db.session import get_session
from app.schemas.contact import ContactCreate, ContactRead
from app.services.contacts import ContactService

settings = get_settings()

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactRead])
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    search: str | None = None,
    owner_id: int | None = Query(default=None, description="Filter by owner (admins only)"),
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = ContactService(session)
    contacts = await service.list_contacts(
        context.organization.id,
        role=context.membership.role,
        page=page,
        page_size=page_size,
        search=search,
        owner_id=owner_id,
    )
    return [ContactRead.model_validate(contact) for contact in contacts]


@router.post("", response_model=ContactRead, status_code=201)
async def create_contact(
    payload: ContactCreate,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = ContactService(session)
    contact = await service.create_contact(
        context.organization.id,
        role=context.membership.role,
        requestor_id=context.membership.user_id,
        data=payload,
    )
    return ContactRead.model_validate(contact)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = ContactService(session)
    await service.delete_contact(
        context.organization.id,
        contact_id,
        role=context.membership.role,
        requestor_id=context.membership.user_id,
    )
    return None
