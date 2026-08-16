import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.analytics import UserStats, DailyActivity, UserSkillScore, LearningEvent
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    DashboardStats,
    HeatmapDataPoint,
    SkillScore,
    RecentActivityItem,
)


class DashboardService:
    @staticmethod
    async def get_overview(user_id: str, db: AsyncSession) -> DashboardOverviewResponse:
        # 1. Overall stats
        stats_res = await db.execute(select(UserStats).filter_by(user_id=user_id))
        stats = stats_res.scalars().first()

        # 2. Daily activity (heatmap) for the last 365 days
        one_year_ago = datetime.datetime.now(datetime.UTC).date() - datetime.timedelta(days=365)
        activity_res = await db.execute(
            select(DailyActivity)
            .filter(DailyActivity.user_id == user_id, DailyActivity.activity_date >= one_year_ago)
            .order_by(DailyActivity.activity_date.asc())
        )
        activities = activity_res.scalars().all()
        heatmap = [
            HeatmapDataPoint(date=a.activity_date.isoformat(), count=a.submissions_count + a.interviews_done)
            for a in activities
            if (a.submissions_count + a.interviews_done) > 0
        ]

        # 3. User skills
        skills_res = await db.execute(select(UserSkillScore).filter_by(user_id=user_id))
        skills = skills_res.scalars().all()

        # 4. Recent learning events
        events_res = await db.execute(
            select(LearningEvent).filter_by(user_id=user_id).order_by(LearningEvent.created_at.desc()).limit(10)
        )
        events = events_res.scalars().all()

        return DashboardOverviewResponse(
            user_id=user_id,
            stats=DashboardStats.model_validate(stats) if stats else None,
            heatmap=heatmap,
            skills=[SkillScore.model_validate(s) for s in skills],
            recent_activity=[RecentActivityItem.model_validate(e) for e in events],
        )
