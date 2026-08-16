from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_jwt
from app.schemas.dashboard import DashboardOverviewResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
):
    user_id = payload.get("sub", "")
    return await DashboardService.get_overview(user_id, db)
