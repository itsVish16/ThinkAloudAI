from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import get_db, get_redis
from app.auth import verify_jwt
from app.schemas.system_design import (
    SystemDesignQuestionCreate,
    SystemDesignQuestionOut,
    SystemDesignSubmitRequest,
    SystemDesignSubmitResponse,
)
from app.services.system_design_service import SystemDesignService

router = APIRouter(prefix="/system-design", tags=["System Design Questions"])


@router.get("/questions", response_model=List[SystemDesignQuestionOut])
async def list_questions(
    domain: Optional[str] = None,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await SystemDesignService.list_questions(db, redis, domain=domain, role=role)


@router.get("/questions/{question_id}", response_model=SystemDesignQuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    return await SystemDesignService.get_question(question_id, db)


@router.post("/questions", response_model=SystemDesignQuestionOut)
async def create_question(
    request: SystemDesignQuestionCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    return await SystemDesignService.create_question(request, db, redis)


@router.post("/questions/{question_id}/submit", response_model=SystemDesignSubmitResponse, dependencies=[Depends(verify_jwt)])
async def submit_system_design(
    question_id: int,
    request: SystemDesignSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    return await SystemDesignService.evaluate_submission(question_id, request, db)
