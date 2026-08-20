import os
import math
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.redis import get_redis
from redis.asyncio import Redis
from app.api.user import get_current_user
from app.models.user import User
from app.models.profile import UserProfile, UserPreference
from app.models.learning import Achievement, UserAchievement
from app.repositories.user_repository import UserRepository
from app.schemas.admin import (
    UserAdminListResponse,
    UserAdminSummary,
    UserAdminDetailResponse,
    UserAdminStatusUpdateRequest,
    AchievementCreateRequest,
)
from app.schemas.profile import ProfileResponse, PreferenceResponse, AchievementResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    admin_emails = os.getenv("ADMIN_EMAILS", "")
    email = current_user.get("email", "")
    allowed = [e.strip().lower() for e in admin_emails.split(",") if e.strip()]
    if not email or not allowed or email.lower() not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/users/stats")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Dict[str, Any]:
    # Total Users
    total_users_query = select(func.count()).select_from(User)
    total_users = (await db.execute(total_users_query)).scalar() or 0

    # Verified Users
    verified_users_query = select(func.count()).select_from(User).where(User.is_verified == True)
    verified_users = (await db.execute(verified_users_query)).scalar() or 0

    # User Growth (Last 30 days)
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    growth_query = (
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= thirty_days_ago)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    growth_result = await db.execute(growth_query)

    growth_data = []
    for row in growth_result.all():
        growth_data.append({
            "date": str(row.date),
            "users": row.count,
        })

    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "unverified_users": total_users - verified_users,
        "growth": growth_data,
    }


@router.get("/users", response_model=UserAdminListResponse)
async def list_users_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    users, total = await UserRepository.list_users(
        db, page=page, limit=limit, search=search, is_verified=is_verified
    )
    pages = math.ceil(total / limit) if total > 0 else 1

    return UserAdminListResponse(
        items=[UserAdminSummary.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/users/{user_id}", response_model=UserAdminDetailResponse)
async def get_user_detail_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    user = await UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch profile
    prof_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()

    # Fetch preferences
    pref_res = await db.execute(select(UserPreference).where(UserPreference.user_id == user.id))
    preferences = pref_res.scalar_one_or_none()

    # Fetch achievements
    ach_stmt = (
        select(Achievement)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user.id)
    )
    ach_res = await db.execute(ach_stmt)
    achievements = ach_res.scalars().all()

    return UserAdminDetailResponse(
        user=UserAdminSummary.model_validate(user),
        profile=ProfileResponse.model_validate(profile) if profile else None,
        preferences=PreferenceResponse.model_validate(preferences) if preferences else None,
        achievements=[AchievementResponse.model_validate(a) for a in achievements],
    )


@router.patch("/users/{user_id}/status")
async def update_user_status_admin(
    user_id: int,
    payload: UserAdminStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(require_admin),
):
    user = await UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.is_verified is not None:
        user.is_verified = payload.is_verified
    if payload.full_name is not None:
        user.full_name = payload.full_name

    await UserRepository.save(db, user)
    
    # Invalidate cache
    try:
        from app.services.cache import delete_cached_user_profile
        await delete_cached_user_profile(redis, user.id)
    except Exception:
        pass

    return {"message": "User status updated successfully", "user_id": user.id, "is_verified": user.is_verified}


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(require_admin),
):
    user = await UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await UserRepository.delete(db, user)

    try:
        from app.services.cache import delete_cached_user_profile
        await delete_cached_user_profile(redis, user_id)
    except Exception:
        pass

    return {"message": "User deleted successfully", "user_id": user_id}


@router.get("/achievements", response_model=List[AchievementResponse])
async def list_achievements_admin(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = await db.execute(select(Achievement).order_by(Achievement.id.asc()))
    achievements = result.scalars().all()
    return [AchievementResponse.model_validate(a) for a in achievements]


@router.post("/achievements", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED)
async def create_achievement_admin(
    payload: AchievementCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    achievement = Achievement(
        title=payload.title,
        description=payload.description,
        icon_url=payload.icon_url,
    )
    db.add(achievement)
    await db.commit()
    await db.refresh(achievement)
    return AchievementResponse.model_validate(achievement)
