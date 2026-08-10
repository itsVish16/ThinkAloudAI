from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import get_db
from app.auth import verify_jwt
from app.models.analytics import UserStats, DailyActivity, UserSkillScore, LearningEvent
from app.schemas.dashboard import DashboardOverviewResponse, DashboardStats, HeatmapDataPoint, SkillScore, RecentActivityItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the unified dashboard analytics for the user.
    """
    user_id = payload.get("sub")

    # 1. Fetch overall stats
    stats_result = await db.execute(select(UserStats).filter_by(user_id=user_id))
    stats = stats_result.scalars().first()
    
    # 2. Fetch daily activity (heatmap) for the last 365 days
    import datetime
    one_year_ago = datetime.datetime.now(datetime.UTC).date() - datetime.timedelta(days=365)
    activity_res = await db.execute(
        select(DailyActivity).filter(DailyActivity.user_id == user_id, DailyActivity.activity_date >= one_year_ago)
        .order_by(DailyActivity.activity_date.asc())
    )
    activities = activity_res.scalars().all()
    heatmap = [
        HeatmapDataPoint(date=a.activity_date.isoformat(), count=a.submissions_count + a.interviews_done)
        for a in activities if (a.submissions_count + a.interviews_done) > 0
    ]

    # 3. Fetch user skills
    skills_res = await db.execute(select(UserSkillScore).filter_by(user_id=user_id))
    skills = skills_res.scalars().all()

    # 4. Fetch recent learning events
    events_res = await db.execute(
        select(LearningEvent).filter_by(user_id=user_id).order_by(LearningEvent.created_at.desc()).limit(10)
    )
    events = events_res.scalars().all()

    # Build Response
    return DashboardOverviewResponse(
        user_id=user_id,
        stats=DashboardStats.model_validate(stats) if stats else None,
        heatmap=heatmap,
        skills=[SkillScore.model_validate(s) for s in skills],
        recent_activity=[RecentActivityItem.model_validate(e) for e in events]
    )
