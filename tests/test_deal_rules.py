from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.enums import DealStage, MemberRole
from app.services.deals import DealService


def test_member_cannot_move_stage_backwards():
    service = DealService(MagicMock())
    with pytest.raises(HTTPException):
        service._validate_stage_transition(DealStage.PROPOSAL, DealStage.QUALIFICATION, MemberRole.MEMBER)


def test_admin_can_move_stage_backwards():
    service = DealService(MagicMock())
    service._validate_stage_transition(DealStage.NEGOTIATION, DealStage.PROPOSAL, MemberRole.ADMIN)
