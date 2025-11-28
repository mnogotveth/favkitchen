from __future__ import annotations

from fastapi import APIRouter, FastAPI

from app.api.routers import activities, analytics, auth, contacts, deals, organizations, tasks
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

api_v1 = APIRouter(prefix=settings.api_v1_prefix)

api_v1.include_router(auth.router)
api_v1.include_router(organizations.router)
api_v1.include_router(contacts.router)
api_v1.include_router(deals.router)
api_v1.include_router(tasks.router)
api_v1.include_router(activities.router)
api_v1.include_router(analytics.router)

app.include_router(api_v1)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
