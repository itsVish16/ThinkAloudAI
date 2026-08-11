import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from sqlalchemy import text

from app.database import get_db, get_redis
from app.models.aiml import AIMLQuestion
from app.schemas.aiml import AIMLQuestionCreate, AIMLQuestionOut
from redis.asyncio import Redis
from app.auth import verify_jwt

router = APIRouter(prefix="/aiml", tags=["AI/ML Questions"], dependencies=[Depends(verify_jwt)])



@router.get("/questions", response_model=List[AIMLQuestionOut])
async def list_questions(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    List all available AI/ML questions.
    """
    cache_key = f"aiml:questions:all"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    query = select(AIMLQuestion).limit(limit)
    result = await db.execute(query)
    questions = result.scalars().all()

    def _serialize(q):
        data = AIMLQuestionOut.model_validate(q).model_dump()
        data["created_at"] = data["created_at"].isoformat()
        return data

    serialized_q = [_serialize(q) for q in questions]
    await redis.set(cache_key, json.dumps(serialized_q), ex=3600)

    return questions

@router.get("/questions/{question_id}", response_model=AIMLQuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific AI/ML question by its ID.
    """
    result = await db.execute(select(AIMLQuestion).filter(AIMLQuestion.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/questions", response_model=AIMLQuestionOut)
async def create_question(
    request: AIMLQuestionCreate, 
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Create a new AI/ML question.
    """
    new_question = AIMLQuestion(
        title=request.title,
        description=request.description,
        domain=request.domain,
        role=request.role
    )
    db.add(new_question)
    await db.commit()
    await db.refresh(new_question)
    
    # Invalidate cache
    await redis.delete("aiml:questions:all")
    
    return new_question
