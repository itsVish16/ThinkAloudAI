import json as _json

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import UserPreference, UserProfile
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import UpdateProfileDetailsRequest, UpdateUserPreferenceRequest
from app.services.user_service import get_user_by_username

FULL_PROFILE_CACHE_TTL = 60


class ProfileService:
    @staticmethod
    def _full_profile_cache_key(user_id: int) -> str:
        return f"user:full_profile:{user_id}"

    @staticmethod
    def _public_profile_cache_key(user_id: int) -> str:
        return f"user:public_profile:{user_id}"

    @staticmethod
    async def get_user_full_profile(current_user: User, db: AsyncSession, redis: Redis) -> dict:
        cache_key = ProfileService._full_profile_cache_key(current_user.id)
        cached = await redis.get(cache_key)
        if cached:
            return _json.loads(cached)

        profile = await ProfileRepository.get_profile_by_user_id(db, current_user.id)
        ach_rows = await ProfileRepository.get_user_achievements(db, current_user.id)

        achievements = [
            {
                "title": a.title,
                "description": a.description,
                "icon_url": a.icon_url,
                "earned_at": earned_at.isoformat(),
            }
            for a, earned_at in ach_rows
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        cache_key = ProfileService._public_profile_cache_key(user.id)
        cached = await redis.get(cache_key)
        if cached:
            return _json.loads(cached)

        profile = await ProfileRepository.get_profile_by_user_id(db, user.id)
        ach_rows = await ProfileRepository.get_user_achievements(db, user.id)

        achievements = [
            {
                "title": a.title,
                "description": a.description,
                "icon_url": a.icon_url,
                "earned_at": earned_at.isoformat(),
            }
            for a, earned_at in ach_rows
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

    @staticmethod
    async def update_profile_details(
        user_id: int,
        payload: UpdateProfileDetailsRequest,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        profile = await ProfileRepository.get_or_create_profile(db, user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)

        await ProfileRepository.save_profile(db, profile)

        # Invalidate profile caches
        await redis.delete(ProfileService._full_profile_cache_key(user_id))
        await redis.delete(ProfileService._public_profile_cache_key(user_id))

        return {"message": "Profile details updated"}

    @staticmethod
    async def get_preferences(user_id: int, db: AsyncSession) -> UserPreference:
        return await ProfileRepository.get_or_create_preferences(db, user_id)

    @staticmethod
    async def update_preferences(
        user_id: int,
        payload: UpdateUserPreferenceRequest,
        db: AsyncSession,
    ) -> UserPreference:
        pref = await ProfileRepository.get_or_create_preferences(db, user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pref, key, value)

        return await ProfileRepository.save_preferences(db, pref)

    @staticmethod
    async def list_achievements(db: AsyncSession) -> list[dict]:
        achievements = await ProfileRepository.get_all_achievements(db)
        return [
            {
                "id": a.id,
                "title": a.title,
                "description": a.description,
                "icon_url": a.icon_url,
            }
            for a in achievements
        ]
