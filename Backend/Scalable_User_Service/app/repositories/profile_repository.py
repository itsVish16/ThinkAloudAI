from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import Achievement, UserAchievement
from app.models.profile import UserPreference, UserProfile


class ProfileRepository:
    """Repository for Profile, Preference, and Achievement data access."""

    @staticmethod
    async def get_profile_by_user_id(db: AsyncSession, user_id: int) -> UserProfile | None:
        result = await db.execute(select(UserProfile).filter_by(user_id=user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_profile(db: AsyncSession, user_id: int) -> UserProfile:
        profile = await ProfileRepository.get_profile_by_user_id(db, user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            await db.commit()
            await db.refresh(profile)
        return profile

    @staticmethod
    async def save_profile(db: AsyncSession, profile: UserProfile) -> UserProfile:
        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def get_preferences_by_user_id(db: AsyncSession, user_id: int) -> UserPreference | None:
        result = await db.execute(select(UserPreference).filter_by(user_id=user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_preferences(db: AsyncSession, user_id: int) -> UserPreference:
        pref = await ProfileRepository.get_preferences_by_user_id(db, user_id)
        if not pref:
            pref = UserPreference(user_id=user_id)
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
        return pref

    @staticmethod
    async def save_preferences(db: AsyncSession, pref: UserPreference) -> UserPreference:
        await db.commit()
        await db.refresh(pref)
        return pref

    @staticmethod
    async def get_all_achievements(db: AsyncSession) -> Sequence[Achievement]:
        result = await db.execute(select(Achievement))
        return result.scalars().all()

    @staticmethod
    async def get_user_achievements(db: AsyncSession, user_id: int) -> list[tuple[Achievement, any]]:
        result = await db.execute(
            select(Achievement, UserAchievement.earned_at)
            .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
            .filter(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.earned_at.desc())
        )
        return list(result.all())
