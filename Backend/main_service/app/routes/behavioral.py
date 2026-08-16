from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func
from app.database import get_db
from app.models.behavioral import BehavioralQuestion
from app.auth import verify_jwt_or_internal

router = APIRouter(prefix="/behavioral", tags=["Behavioral Interviews"])


@router.get("/questions", dependencies=[Depends(verify_jwt_or_internal)])
async def get_behavioral_questions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetch behavioral questions from the database."""
    query = select(BehavioralQuestion).order_by(func.random()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
