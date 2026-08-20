from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Repository for User database operations."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def save(db: AsyncSession, user: User) -> User:
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.commit()

    @staticmethod
    async def list_users(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        is_verified: bool | None = None,
    ) -> tuple[list[User], int]:
        from sqlalchemy import func, or_
        query = select(User)

        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)

        if search:
            search_pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(User.username).like(search_pattern),
                    func.lower(User.email).like(search_pattern),
                    func.lower(User.full_name).like(search_pattern),
                )
            )

        # Count total matching
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        offset = max(0, (page - 1) * limit)
        paginated_query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(paginated_query)
        items = list(result.scalars().all())

        return items, total
