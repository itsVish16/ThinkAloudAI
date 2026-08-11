from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from redis.asyncio import Redis

from app.database import get_db, get_redis
from app.auth import verify_jwt
from app.schemas.dsa import (
    DSAQuestionCreate, DSAQuestionOut, CodeSubmitRequest, 
    CodeSubmitResponse, CodeSubmissionOut, UserProblemStatusOut, RecommendationOut
)
from app.services.dsa_service import DSAService

router = APIRouter(prefix="/dsa", tags=["DSA Questions"])

def get_current_user_id(payload: dict = Depends(verify_jwt)) -> str:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token payload: 'sub' missing")
    return user_id

@router.get("/debug/median")
async def get_median_debug(db: AsyncSession = Depends(get_db)):
    return await DSAService.get_median_debug(db)

@router.get("/questions", response_model=List[DSAQuestionOut])
async def list_questions(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    return await DSAService.list_questions(db, redis, skip, limit)

@router.get("/questions/{question_id}", response_model=DSAQuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    return await DSAService.get_question(question_id, db)

@router.post("/questions", response_model=DSAQuestionOut)
async def create_question(
    request: DSAQuestionCreate, 
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await DSAService.create_question(request, db, redis)

@router.get("/questions/{question_id}/submission", response_model=Optional[CodeSubmissionOut])
async def get_latest_submission(
    question_id: int, 
    language: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id), 
    db: AsyncSession = Depends(get_db)
):
    return await DSAService.get_latest_submission(question_id, language, user_id, db)

@router.post("/questions/{question_id}/run", response_model=CodeSubmitResponse, dependencies=[Depends(verify_jwt)])
async def run_solution(
    question_id: int, 
    request: CodeSubmitRequest, 
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await DSAService.run_solution(question_id, request, db, redis)

@router.post("/questions/{question_id}/submit", response_model=CodeSubmitResponse, dependencies=[Depends(verify_jwt)])
async def submit_solution(
    question_id: int, 
    request: CodeSubmitRequest, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await DSAService.submit_solution(question_id, request, db, redis)

@router.get("/submissions/{submission_id}/stream")
async def stream_submission_status(submission_id: int):
    return DSAService.stream_submission_status(submission_id)

@router.get("/submissions/{session_id}", response_model=List[CodeSubmissionOut])
async def get_session_submissions(session_id: str, db: AsyncSession = Depends(get_db)):
    return await DSAService.get_session_submissions(session_id, db)

@router.get("/questions/{question_id}/submissions/{session_id}", response_model=List[CodeSubmissionOut])
async def get_question_submissions(question_id: int, session_id: str, db: AsyncSession = Depends(get_db)):
    return await DSAService.get_question_submissions(question_id, session_id, db)

@router.get("/status", response_model=List[UserProblemStatusOut])
async def get_user_dsa_status(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return await DSAService.get_user_dsa_status(db, user_id)

@router.get("/recommendations", response_model=List[RecommendationOut])
async def get_user_recommendations(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return await DSAService.get_user_recommendations(db, user_id)
