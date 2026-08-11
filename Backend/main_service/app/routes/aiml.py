import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db, get_redis
from app.schemas.aiml import AIMLQuestionCreate, AIMLQuestionOut
from redis.asyncio import Redis
from app.auth import verify_jwt
from app.services.aiml_service import AIMLService

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
    return await AIMLService.list_questions(limit, db, redis)

@router.get("/questions/{question_id}", response_model=AIMLQuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific AI/ML question by its ID.
    """
    return await AIMLService.get_question(question_id, db)

@router.post("/questions", response_model=AIMLQuestionOut)
async def create_question(
    request: AIMLQuestionCreate, 
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Create a new AI/ML question.
    """
    return await AIMLService.create_question(request, db, redis)
