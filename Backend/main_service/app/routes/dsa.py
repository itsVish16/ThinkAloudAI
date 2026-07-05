from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import asyncio

from app.database import get_db, get_redis
from app.models.dsa import DSAQuestion, CodeSubmission
from app.schemas.dsa import DSAQuestionCreate, DSAQuestionOut, CodeSubmitRequest, CodeSubmitResponse, CodeSubmissionOut

router = APIRouter(prefix="/dsa", tags=["DSA Questions"])

@router.get("/debug/median")
async def get_median_debug(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DSAQuestion).filter(DSAQuestion.title == "Median of Two Sorted Arrays"))
    q = result.scalar_one_or_none()
    if q:
        return {"raw": q.description}
    return {"raw": "not found"}


def get_current_user_id() -> str:
    return "test_user_id"

from redis.asyncio import Redis
import json

@router.get("/questions", response_model=List[DSAQuestionOut])
async def list_questions(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    cache_key = "dsa:questions:all"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await db.execute(select(DSAQuestion))
    questions = result.scalars().all()

    # Serialize using the pydantic model to dict, then json string
    # We must format datetime properly for JSON serialization
    def _serialize(q):
        data = DSAQuestionOut.model_validate(q).model_dump()
        data["created_at"] = data["created_at"].isoformat()
        return data

    serialized_q = [_serialize(q) for q in questions]
    await redis.set(cache_key, json.dumps(serialized_q), ex=3600)

    return questions

@router.get("/questions/{question_id}", response_model=DSAQuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DSAQuestion).filter(DSAQuestion.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/questions", response_model=DSAQuestionOut)
async def create_question(request: DSAQuestionCreate, db: AsyncSession = Depends(get_db)):
    new_question = DSAQuestion(
        title=request.title,
        description=request.description,
        difficulty=request.difficulty,
        test_cases=request.test_cases,
        python_starter_code=request.python_starter_code,
        cpp_starter_code=request.cpp_starter_code
    )
    db.add(new_question)
    await db.commit()
    await db.refresh(new_question)
    return new_question

@router.get("/questions/{question_id}/submission", response_model=Optional[CodeSubmissionOut])
async def get_latest_submission(
    question_id: int, 
    language: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id), 
    db: AsyncSession = Depends(get_db)
):
    query = select(CodeSubmission).filter(
        CodeSubmission.question_id == question_id,
        CodeSubmission.session_id == user_id
    )
    if language:
        query = query.filter(CodeSubmission.language == language)
        
    query = query.order_by(CodeSubmission.created_at.desc())
    result = await db.execute(query)
    return result.scalars().first()

@router.post("/questions/{question_id}/run", response_model=CodeSubmitResponse)
async def run_solution(question_id: int, request: CodeSubmitRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DSAQuestion).filter(DSAQuestion.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    from app.services.docker_runner import run_code_in_docker
    
    # Ideally run_code_in_docker would be async, running it synchronously for now
    docker_result = run_code_in_docker(
        code=request.code,
        function_name=question.function_name,
        test_cases_json=question.test_cases,
        language=request.language,
        test_harness=question.cpp_test_harness
    )
    
    submission = CodeSubmission(
        session_id=request.session_id,
        question_id=question_id,
        code=request.code,
        language=request.language,
        status=docker_result["status"],
        error_message=docker_result.get("error_message"),
        is_submission=False
    )
    db.add(submission)
    await db.commit()
    
    return CodeSubmitResponse(**docker_result)

@router.post("/questions/{question_id}/submit", response_model=CodeSubmitResponse)
async def submit_solution(question_id: int, request: CodeSubmitRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DSAQuestion).filter(DSAQuestion.id == question_id))
    question = result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    from app.services.docker_runner import run_code_in_docker
    
    docker_result = run_code_in_docker(
        code=request.code,
        function_name=question.function_name,
        test_cases_json=question.test_cases,
        language=request.language,
        test_harness=question.cpp_test_harness
    )
    
    submission = CodeSubmission(
        session_id=request.session_id,
        question_id=question_id,
        code=request.code,
        language=request.language,
        status=docker_result["status"],
        error_message=docker_result.get("error_message"),
        is_submission=True
    )
    db.add(submission)
    await db.commit()
    
    if docker_result["status"] == "Accepted":
        from app.services.event_bus import publish_event
        from app.models.user_replica import UserProfileReplica
        
        replica_result = await db.execute(
            select(UserProfileReplica).filter(UserProfileReplica.id == request.session_id)
        )
        replica = replica_result.scalars().first()
        resolved_user_id = int(replica.id) if replica else None
        
        async def fire_event():
            try:
                wrapped_payload = {
                    "event": "ProblemSolved",
                    "data": {
                        "user_id": resolved_user_id,
                        "problem_id": question_id,
                        "question_title": question.title,
                        "language": request.language,
                        "session_id": request.session_id,
                        "difficulty": question.difficulty,
                        "score_change": 10 if question.difficulty == "Easy" else 20 if question.difficulty == "Medium" else 30
                    }
                }
                await publish_event("main_events", wrapped_payload)
            except Exception as e:
                import logging
                logging.error(f"Failed to fire event: {e}")
                
        background_tasks.add_task(fire_event)
    
    return CodeSubmitResponse(**docker_result)

@router.get("/submissions/{session_id}", response_model=List[CodeSubmissionOut])
async def get_session_submissions(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CodeSubmission)
        .filter(CodeSubmission.session_id == session_id, CodeSubmission.is_submission == True)
        .order_by(CodeSubmission.created_at.desc())
    )
    return result.scalars().all()

@router.get("/questions/{question_id}/submissions/{session_id}", response_model=List[CodeSubmissionOut])
async def get_question_submissions(question_id: int, session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CodeSubmission)
        .filter(CodeSubmission.question_id == question_id)
        .filter(CodeSubmission.session_id == session_id)
        .filter(CodeSubmission.is_submission == True)
        .order_by(CodeSubmission.created_at.desc())
    )
    return result.scalars().all()

from app.models.dsa import UserProblemStatus
from app.schemas.dsa import UserProblemStatusOut

@router.get("/status", response_model=List[UserProblemStatusOut])
async def get_user_dsa_status(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    Get the completion status for all DSA problems for the current user.
    """
    result = await db.execute(
        select(UserProblemStatus)
        .filter(UserProblemStatus.user_id == user_id)
    )
    return result.scalars().all()

from app.models.dsa import Recommendation
from app.schemas.dsa import RecommendationOut

@router.get("/recommendations", response_model=List[RecommendationOut])
async def get_user_recommendations(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """
    Get AI-generated problem recommendations for the current user.
    """
    result = await db.execute(
        select(Recommendation)
        .filter(Recommendation.user_id == user_id)
        .order_by(Recommendation.created_at.desc())
    )
    return result.scalars().all()
