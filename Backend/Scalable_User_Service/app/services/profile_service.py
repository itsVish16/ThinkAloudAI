import json as _json
from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserProfile, UserPreference
from app.models.learning import Achievement, UserAchievement
from app.schemas.profile import UpdateProfileDetailsRequest, UpdatePreferencesRequest
from app.services.user_service import get_user_by_username

FULL_PROFILE_CACHE_TTL = 60

class ProfileService:
    
    @staticmethod
    def _full_profile_cache_key(user_id: int) -> str:
        return f"user:full_profile:{user_id}"

    @staticmethod
    async def get_user_full_profile(current_user: User, db: AsyncSession, redis: Redis) -> dict:
        cache_key = ProfileService._full_profile_cache_key(current_user.id)
        cached = await redis.get(cache_key)
        if cached:
            return _json.loads(cached)

        profile_res = await db.execute(select(UserProfile).filter_by(user_id=current_user.id))
        profile = profile_res.scalar_one_or_none()

        ach_res = await db.execute(
            select(Achievement, UserAchievement.earned_at)
            .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
            .filter(UserAchievement.user_id == current_user.id)
            .order_by(UserAchievement.earned_at.desc())
        )
        achievements = [
            {"title": a.title, "description": a.description, "icon_url": a.icon_url, "earned_at": earned_at.isoformat()}
            for a, earned_at in ach_res.all()
        ]

        response_data = {
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat(),

            "bio": profile.bio if profile else None,
            "avatar_url": profile.avatar_url if profile else None,
            "github_url": profile.github_url if profile else None,
            "linkedin_url": profile.linkedin_url if profile else None,
            "headline": profile.headline if profile else None,
            "location": profile.location if profile else None,
            "institution": profile.institution if profile else None,
            "preferred_language": profile.preferred_language if profile else None,
            "resume_url": profile.resume_url if profile else None,

            "achievements": achievements,
        }

        await redis.setex(cache_key, FULL_PROFILE_CACHE_TTL, _json.dumps(response_data))
        return response_data

    @staticmethod
    async def get_public_profile(username: str, db: AsyncSession, redis: Redis) -> dict:
        user = await get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        cache_key = f"user:public_profile:{user.id}"
        cached = await redis.get(cache_key)
        if cached:
            return _json.loads(cached)

        profile_res = await db.execute(select(UserProfile).filter_by(user_id=user.id))
        profile = profile_res.scalar_one_or_none()

        ach_res = await db.execute(
            select(Achievement, UserAchievement.earned_at)
            .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
            .filter(UserAchievement.user_id == user.id)
            .order_by(UserAchievement.earned_at.desc())
        )
        achievements = [
            {"title": a.title, "description": a.description, "icon_url": a.icon_url, "earned_at": earned_at.isoformat()}
            for a, earned_at in ach_res.all()
        ]

        response_data = {
            "username": user.username,
            "full_name": user.full_name,
            "bio": profile.bio if profile else None,
            "avatar_url": profile.avatar_url if profile else None,
            "github_url": profile.github_url if profile else None,
            "linkedin_url": profile.linkedin_url if profile else None,
            "headline": profile.headline if profile else None,
            "location": profile.location if profile else None,
            "institution": profile.institution if profile else None,
            "preferred_language": profile.preferred_language if profile else None,
            "achievements": achievements,
        }

        await redis.setex(cache_key, FULL_PROFILE_CACHE_TTL, _json.dumps(response_data))
        return response_data
