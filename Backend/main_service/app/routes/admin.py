import os
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_jwt
from app.models.dsa import CodeSubmission, DSAQuestion
from app.models.roadmap import Roadmap

router = APIRouter(prefix="/admin", tags=["admin"])

async def require_admin(payload: dict = Depends(verify_jwt), db: AsyncSession = Depends(get_db)) -> dict:
    user_id = payload.get("sub")
    # Get user email directly from JWT
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

    email = email or "unknown@domain.com"
    admin_emails = os.getenv("ADMIN_EMAILS", "vishal@example.com,vishal@thinkaloud.ai,vishalsaini160204@gmail.com")
    
    if not admin_emails or email.lower() not in [e.strip().lower() for e in admin_emails.split(",") if e.strip()]:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
        
    return payload

import json
from app.database import get_db, get_redis
from redis.asyncio import Redis
from sqlalchemy import or_

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
    
    # Success rate (support both legacy 'Passed' and modern 'Accepted' statuses)
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
