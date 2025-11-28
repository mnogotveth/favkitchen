from __future__ import annotations

from datetime import date, datetime, time, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ActivityType, MemberRole
from app.models.models import Activity, Deal, Task
from app.repositories.deal_repository import DealRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TaskRepository(session)
        self.deals = DealRepository(session)

    async def list_tasks(
        self,
        organization_id: int,
        *,
        deal_id: int | None,
        only_open: bool,
        due_before: datetime | None,
        due_after: datetime | None,
    ) -> list[Task]:
        return await self.repo.list(
            organization_id,
            deal_id=deal_id,
            only_open=only_open,
            due_before=due_before,
            due_after=due_after,
        )

    async def create_task(
        self,
        organization_id: int,
        user_id: int,
        role: MemberRole,
        data: TaskCreate,
    ) -> Task:
        due_date = _ensure_future_due_date(data.due_date)
        deal = await self.deals.get(organization_id, data.deal_id)
        if not deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        if role == MemberRole.MEMBER and deal.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        task = Task(
            deal_id=deal.id,
            title=data.title,
            description=data.description,
            due_date=due_date,
        )
        await self.repo.create(task)
        await self.session.flush()
        activity = Activity(
            deal_id=deal.id,
            author_id=user_id,
            type=ActivityType.TASK_CREATED,
            payload={"task_id": task.id, "title": task.title},
        )
        self.session.add(activity)
        await self.session.commit()
        return task

    async def update_task(
        self,
        organization_id: int,
        task_id: int,
        *,
        role: MemberRole,
        user_id: int,
        data: TaskUpdate,
    ) -> Task:
        task = await self.repo.get(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        deal = await self.deals.get(organization_id, task.deal_id)
        if not deal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
        if role == MemberRole.MEMBER and deal.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.due_date is not None:
            task.due_date = _ensure_future_due_date(data.due_date)
        if data.is_done is not None:
            task.is_done = data.is_done
        await self.session.commit()
        return task


def _ensure_future_due_date(due: date) -> datetime:
    today = date.today()
    if due < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Due date cannot be in the past"
        )
    return datetime.combine(due, time.min, tzinfo=timezone.utc)
