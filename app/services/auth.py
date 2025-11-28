from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_token, get_password_hash, verify_password
from app.models.enums import MemberRole
from app.models.models import Organization, OrganizationMember, User
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.organizations = OrganizationRepository(session)
        self.settings = get_settings()

    async def register(self, data: RegisterRequest) -> TokenPair:
        existing = await self.users.get_by_email(data.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email exists")

        user = User(email=data.email, hashed_password=get_password_hash(data.password), name=data.name)
        organization = Organization(name=data.organization_name)
        membership = OrganizationMember(user=user, organization=organization, role=MemberRole.OWNER)

        await self.users.add(user)
        await self.organizations.create(organization)
        await self.organizations.add_member(membership)
        await self.session.commit()

        return self._issue_tokens(user.id)

    async def login(self, data: LoginRequest) -> TokenPair:
        user = await self.users.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return self._issue_tokens(user.id)

    def _issue_tokens(self, user_id: int) -> TokenPair:
        access = create_token(
            str(user_id),
            token_type="access",
            expires_delta=timedelta(minutes=self.settings.token.access_token_expire_minutes),
        )
        refresh = create_token(
            str(user_id),
            token_type="refresh",
            expires_delta=timedelta(minutes=self.settings.token.refresh_token_expire_minutes),
        )
        return TokenPair(access_token=access, refresh_token=refresh)
