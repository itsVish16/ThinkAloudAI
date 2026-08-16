import os
from datetime import datetime, timedelta, UTC
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.user import get_current_user
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    admin_emails = os.getenv("ADMIN_EMAILS", "vishal@example.com,vishal@thinkaloud.ai,vishalsaini160204@gmail.com")
    email = current_user.get("email", "")
    if not email or email.lower() not in [e.strip().lower() for e in admin_emails.split(",") if e.strip()]:
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
