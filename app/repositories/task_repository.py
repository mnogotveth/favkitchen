from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.models.models import Deal, Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    async def list(
        self,
        organization_id: int,
        *,
        deal_id: int | None = None,
        only_open: bool = False,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
    ) -> list[Task]:
        stmt = select(Task).join(Deal).where(Deal.organization_id == organization_id)
        if deal_id:
            stmt = stmt.where(Task.deal_id == deal_id)
        if only_open:
            stmt = stmt.where(Task.is_done.is_(False))
        if due_before:
            stmt = stmt.where(Task.due_date <= due_before)
        if due_after:
            stmt = stmt.where(Task.due_date >= due_after)
        stmt = stmt.order_by(Task.due_date.asc())
        rows = await self.session.scalars(stmt)
        return list(rows.all())

    async def create(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        return await self.session.scalar(stmt)
