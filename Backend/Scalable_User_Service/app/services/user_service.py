from datetime import UTC, datetime

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import SignupRequest, UpdateUserRequest, UserResponse
from app.services.cache import delete_cached_user_profile, set_cached_user_profile


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await UserRepository.get_by_email(db, email)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    return await UserRepository.get_by_username(db, username)


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await UserRepository.get_by_id(db, user_id)


async def create_user(db: AsyncSession, payload: SignupRequest, password_hash: str) -> User:
    user = User(
        username=payload.username,
        email=str(payload.email),
        full_name=payload.full_name,
        password_hash=password_hash,
        is_verified=False,
    )
    return await UserRepository.create(db, user)


async def check_user_password(user: User, password: str) -> bool:
    return await verify_password(password, user.password_hash)


async def update_user(
    db: AsyncSession,
    user: User,
    payload: UpdateUserRequest,
) -> User:
    if payload.username is not None:
        user.username = payload.username

    if payload.full_name is not None:
        user.full_name = payload.full_name

    try:
        return await UserRepository.save(db, user)
    except IntegrityError:
        await db.rollback()
        raise


async def update_user_password(db: AsyncSession, user: User, password_hash: str) -> User:
    user.password_hash = password_hash
    try:
        return await UserRepository.save(db, user)
    except IntegrityError:
        await db.rollback()
        raise


async def mark_user_verified(db: AsyncSession, user: User) -> User:
    user.is_verified = True
    try:
        return await UserRepository.save(db, user)
    except IntegrityError:
        await db.rollback()
        raise


async def update_last_login(db: AsyncSession, user: User) -> None:
    user.last_login_at = datetime.now(UTC)
    await UserRepository.save(db, user)


class UserService:
    @staticmethod
    async def update_me(
        user: User,
        payload: UpdateUserRequest,
        db: AsyncSession,
        redis: Redis,
    ) -> dict:
        try:
            updated_user = await update_user(db, user, payload)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )

        # Publish event
        await redis.publish("user_events", f"user.updated:{updated_user.id}")

        # Invalidate and refresh cache
        await delete_cached_user_profile(redis, updated_user.id)
        response_data = UserResponse.model_validate(updated_user).model_dump(mode="json")
        await set_cached_user_profile(redis, updated_user.id, response_data)

        return response_data
