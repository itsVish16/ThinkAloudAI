from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func
from app.database import get_db
from app.models.aiml import AIMLQuestion
from app.auth import verify_jwt_or_internal

router = APIRouter(prefix="/aiml", tags=["AI/ML Engineering Interviews"])


@router.get("/questions", dependencies=[Depends(verify_jwt_or_internal)])
async def get_aiml_questions(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Fetch AI/ML questions from the database."""
    query = select(AIMLQuestion).order_by(func.random()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
