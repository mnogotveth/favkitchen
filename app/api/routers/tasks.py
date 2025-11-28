from __future__ import annotations

from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import OrganizationContext, get_current_member
from app.db.session import get_session
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.tasks import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    deal_id: int | None = None,
    only_open: bool = False,
    due_before: date | None = Query(default=None),
    due_after: date | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = TaskService(session)
    tasks = await service.list_tasks(
        context.organization.id,
        deal_id=deal_id,
        only_open=only_open,
        due_before=_to_datetime(due_before, end_of_day=True),
        due_after=_to_datetime(due_after, end_of_day=False),
    )
    return [TaskRead.model_validate(task) for task in tasks]


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = TaskService(session)
    task = await service.create_task(
        context.organization.id,
        user_id=context.membership.user_id,
        role=context.membership.role,
        data=payload,
    )
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: AsyncSession = Depends(get_session),
    context: OrganizationContext = Depends(get_current_member),
):
    service = TaskService(session)
    task = await service.update_task(
        context.organization.id,
        task_id,
        role=context.membership.role,
        user_id=context.membership.user_id,
        data=payload,
    )
    return TaskRead.model_validate(task)


def _to_datetime(value: date | None, *, end_of_day: bool) -> datetime | None:
    if value is None:
        return None
    target_time = time.max if end_of_day else time.min
    return datetime.combine(value, target_time, tzinfo=timezone.utc)
