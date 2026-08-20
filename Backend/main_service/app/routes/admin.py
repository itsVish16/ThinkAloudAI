import os
import math
import json
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import get_db, get_redis
from app.auth import verify_jwt
from app.config import settings
from app.models.dsa import CodeSubmission, DSAQuestion
from app.models.roadmap import Roadmap
from app.schemas.dsa import (
    DSAQuestionCreate,
    DSAQuestionOut,
    CodeSubmissionOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(payload: dict = Depends(verify_jwt), db: AsyncSession = Depends(get_db)) -> dict:
    email = payload.get("email")
    
    if not email and payload.get("raw_token"):
        try:
            user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8000")
            from app.core.http_client import http_client
            resp = await http_client.get(
                f"{user_service_url}/api/v1/users/me",
                headers={"Authorization": f"Bearer {payload['raw_token']}"},
                timeout=5.0
            )
            if resp.status_code == 200:
                email = resp.json().get("email", email)
        except Exception:
            pass

    admin_emails = os.getenv("ADMIN_EMAILS", settings.ADMIN_EMAILS)
    allowed = [e.strip().lower() for e in admin_emails.split(",") if e.strip()]
    if not allowed or not email or email.lower() not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
        
    return payload


# ---------------------------------------------------------------------------
# Analytics Stats Endpoints
# ---------------------------------------------------------------------------

@router.get("/coding/stats")
async def get_coding_stats(
    db: AsyncSession = Depends(get_db), 
    redis: Redis = Depends(get_redis),
    _: dict = Depends(require_admin)
):
    cache_key = "admin:coding:stats"
    cached = await redis.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    # Total questions
    total_questions = await db.scalar(select(func.count(DSAQuestion.id)))
    
    # Submissions vs Runs
    total_runs = await db.scalar(select(func.count(CodeSubmission.id)).where(CodeSubmission.is_submission == False))
    total_submissions = await db.scalar(select(func.count(CodeSubmission.id)).where(CodeSubmission.is_submission == True))
    
    # Success rate
    passed_subs = await db.scalar(
        select(func.count(CodeSubmission.id))
        .where(or_(CodeSubmission.status == 'Passed', CodeSubmission.status == 'Accepted'))
    )
    
    # Most attempted
    popular_stmt = (
        select(DSAQuestion.title, func.count(CodeSubmission.id).label("attempts"))
        .join(CodeSubmission, CodeSubmission.question_id == DSAQuestion.id)
        .group_by(DSAQuestion.title)
        .order_by(func.count(CodeSubmission.id).desc())
        .limit(5)
    )
    popular_res = await db.execute(popular_stmt)
    popular_problems = [{"title": row.title, "attempts": row.attempts} for row in popular_res.all()]
    
    stats_data = {
        "total_questions": total_questions or 0,
        "runs": total_runs or 0,
        "submissions": total_submissions or 0,
        "passed_submissions": passed_subs or 0,
        "popular_problems": popular_problems
    }

    try:
        await redis.set(cache_key, json.dumps(stats_data), ex=300)
    except Exception:
        pass

    return stats_data


@router.get("/roadmaps/stats")
async def get_roadmap_stats(
    db: AsyncSession = Depends(get_db), 
    redis: Redis = Depends(get_redis),
    _: dict = Depends(require_admin)
):
    cache_key = "admin:roadmaps:stats"
    cached = await redis.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    total_roadmaps = await db.scalar(select(func.count(Roadmap.id)))
    
    # 30-day trends
    thirty_days_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
    trend_stmt = (
        select(
            func.date(Roadmap.created_at).label("date"),
            func.count(Roadmap.id).label("count")
        )
        .where(Roadmap.created_at >= thirty_days_ago)
        .group_by(func.date(Roadmap.created_at))
        .order_by(func.date(Roadmap.created_at))
    )
    trend_res = await db.execute(trend_stmt)
    growth = [{"date": str(row.date), "roadmaps": row.count} for row in trend_res.all()]
    
    stats_data = {
        "total_roadmaps": total_roadmaps or 0,
        "growth": growth
    }

    try:
        await redis.set(cache_key, json.dumps(stats_data), ex=300)
    except Exception:
        pass

    return stats_data


# ---------------------------------------------------------------------------
# DSA Questions Admin CRUD
# ---------------------------------------------------------------------------

@router.get("/dsa/questions")
async def list_dsa_questions_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    query = select(DSAQuestion)
    if difficulty:
        query = query.where(func.lower(DSAQuestion.difficulty) == difficulty.lower())
    if search:
        search_pattern = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(DSAQuestion.title).like(search_pattern),
                func.lower(DSAQuestion.description).like(search_pattern),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = max(0, (page - 1) * limit)
    paginated_query = query.order_by(DSAQuestion.id.asc()).offset(offset).limit(limit)
    res = await db.execute(paginated_query)
    items = res.scalars().all()

    pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "items": [DSAQuestionOut.model_validate(q) for q in items],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.post("/dsa/questions", response_model=DSAQuestionOut, status_code=status.HTTP_201_CREATED)
async def create_dsa_question_admin(
    payload: DSAQuestionCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _: dict = Depends(require_admin),
):
    question = DSAQuestion(
        title=payload.title,
        description=payload.description,
        difficulty=payload.difficulty,
        test_cases=payload.test_cases,
        python_starter_code=payload.python_starter_code,
        cpp_starter_code=payload.cpp_starter_code,
        cpp_test_harness=payload.cpp_test_harness,
        function_name=payload.function_name,
        hints=payload.hints,
        optimal_time_complexity=payload.optimal_time_complexity,
        optimal_space_complexity=payload.optimal_space_complexity,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)

    # Invalidate cache
    try:
        async for key in redis.scan_iter("dsa:questions:all:*"):
            await redis.delete(key)
    except Exception:
        pass

    return DSAQuestionOut.model_validate(question)


@router.get("/dsa/questions/{question_id}", response_model=DSAQuestionOut)
async def get_dsa_question_admin(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    res = await db.execute(select(DSAQuestion).where(DSAQuestion.id == question_id))
    question = res.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return DSAQuestionOut.model_validate(question)


@router.put("/dsa/questions/{question_id}", response_model=DSAQuestionOut)
async def update_dsa_question_admin(
    question_id: int,
    payload: DSAQuestionCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _: dict = Depends(require_admin),
):
    res = await db.execute(select(DSAQuestion).where(DSAQuestion.id == question_id))
    question = res.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.title = payload.title
    question.description = payload.description
    question.difficulty = payload.difficulty
    question.test_cases = payload.test_cases
    question.python_starter_code = payload.python_starter_code
    question.cpp_starter_code = payload.cpp_starter_code
    question.cpp_test_harness = payload.cpp_test_harness
    question.function_name = payload.function_name
    question.hints = payload.hints
    question.optimal_time_complexity = payload.optimal_time_complexity
    question.optimal_space_complexity = payload.optimal_space_complexity

    await db.commit()
    await db.refresh(question)

    # Invalidate caches
    try:
        await redis.delete(f"dsa:question:{question_id}")
        async for key in redis.scan_iter("dsa:questions:all:*"):
            await redis.delete(key)
    except Exception:
        pass

    return DSAQuestionOut.model_validate(question)


@router.delete("/dsa/questions/{question_id}")
async def delete_dsa_question_admin(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    _: dict = Depends(require_admin),
):
    res = await db.execute(select(DSAQuestion).where(DSAQuestion.id == question_id))
    question = res.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await db.delete(question)
    await db.commit()

    # Invalidate caches
    try:
        await redis.delete(f"dsa:question:{question_id}")
        async for key in redis.scan_iter("dsa:questions:all:*"):
            await redis.delete(key)
    except Exception:
        pass

    return {"message": "Question deleted successfully", "question_id": question_id}


# ---------------------------------------------------------------------------
# Global Submissions Inspector
# ---------------------------------------------------------------------------

@router.get("/dsa/submissions")
async def list_dsa_submissions_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    question_id: Optional[int] = Query(None),
    session_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    query = select(CodeSubmission)
    if status:
        query = query.where(func.lower(CodeSubmission.status) == status.lower())
    if question_id:
        query = query.where(CodeSubmission.question_id == question_id)
    if session_id:
        query = query.where(CodeSubmission.session_id == session_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = max(0, (page - 1) * limit)
    paginated_query = query.order_by(CodeSubmission.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(paginated_query)
    items = res.scalars().all()

    pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "items": [CodeSubmissionOut.model_validate(s) for s in items],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/dsa/submissions/{submission_id}", response_model=CodeSubmissionOut)
async def get_dsa_submission_detail_admin(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    res = await db.execute(select(CodeSubmission).where(CodeSubmission.id == submission_id))
    submission = res.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return CodeSubmissionOut.model_validate(submission)
