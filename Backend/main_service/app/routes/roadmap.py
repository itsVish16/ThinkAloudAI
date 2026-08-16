from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_jwt
from app.schemas.roadmap import (
    RoadmapCreate,
    RoadmapOut,
    ScheduledInterviewOut,
)
from app.services.roadmap_service import RoadmapService

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


def get_current_user_id(payload: dict = Depends(verify_jwt)) -> str:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token payload: 'sub' missing")
    return user_id


@router.get("/interviews/scheduled", response_model=List[ScheduledInterviewOut])
async def get_scheduled_interviews(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await RoadmapService.get_scheduled_interviews(db, user_id)


@router.get("", response_model=List[RoadmapOut])
async def get_user_roadmaps(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await RoadmapService.get_user_roadmaps(db, user_id)


@router.get("/{roadmap_id}", response_model=RoadmapOut)
async def get_roadmap(
    roadmap_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await RoadmapService.get_roadmap(roadmap_id, db, user_id)


@router.post("/", response_model=RoadmapOut)
async def create_roadmap(
    request: RoadmapCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await RoadmapService.create_roadmap(request, db, user_id)


@router.patch("/items/{item_id}/toggle")
async def toggle_roadmap_item(
    item_id: int,
    is_completed: bool,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await RoadmapService.toggle_item(item_id, is_completed, db, user_id)


@router.delete("/{roadmap_id}")
async def delete_roadmap(
    roadmap_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await RoadmapService.delete_roadmap(roadmap_id, db, user_id)
