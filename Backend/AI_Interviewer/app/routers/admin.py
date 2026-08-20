from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import os
import math
import json
import logging
from datetime import datetime, timedelta, UTC

from app.services.db import get_db
from app.models.interview import InterviewSession, UserProfileReplica, InterviewFeedback, InterviewMessage
from app.services.auth import get_current_user
from app.config import settings

logger = logging.getLogger("admin_router")

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_admin(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    email = current_user.get("email")
    if current_user.get("raw_token") and not email:
        try:
            user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8000")
            from app.services.http_client import http_client
            resp = await http_client.get(
                f"{user_service_url}/api/v1/users/me",
                headers={"Authorization": f"Bearer {current_user['raw_token']}"},
                timeout=5.0
            )
            if resp.status_code == 200:
                email = resp.json().get("email", email)
        except Exception as e:
            logger.error(f"Failed to fetch user email from user-service: {e}")

    admin_emails = os.getenv("ADMIN_EMAILS", settings.ADMIN_EMAILS)
    if not email:
        raise HTTPException(status_code=403, detail="Not authorized. No email found.")
    
    allowed = [e.strip().lower() for e in admin_emails.split(",") if e.strip()]
    if not allowed or email.lower() not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
        
    return current_user


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class ScoreOverrideRequest(BaseModel):
    technical_score: Optional[int] = Field(None, ge=0, le=100)
    communication_score: Optional[int] = Field(None, ge=0, le=100)
    english_score: Optional[int] = Field(None, ge=0, le=100)
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Admin Endpoints
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db), _: dict = Depends(require_admin)):
    total_users = await db.scalar(select(func.count(UserProfileReplica.id)))
    total_interviews = await db.scalar(select(func.count(InterviewSession.id)))
    
    time_stmt = select(
        func.sum(func.extract('epoch', InterviewSession.updated_at - InterviewSession.created_at))
    ).where(InterviewSession.stage == 'completed')
    total_seconds = await db.scalar(time_stmt)
    total_minutes = (total_seconds or 0) / 60.0
    
    cat_stmt = select(
        InterviewSession.interview_type, 
        func.count(InterviewSession.id)
    ).where(InterviewSession.stage == 'completed').group_by(InterviewSession.interview_type)
    cat_res = await db.execute(cat_stmt)
    categories = {row[0] or "Unknown": row[1] for row in cat_res.all()}
            
    thirty_days_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
    trend_stmt = (
        select(
            func.date(InterviewSession.created_at).label("date"),
            func.count(InterviewSession.id).label("count")
        )
        .where(InterviewSession.created_at >= thirty_days_ago)
        .group_by(func.date(InterviewSession.created_at))
        .order_by(func.date(InterviewSession.created_at))
    )
    trend_res = await db.execute(trend_stmt)
    growth = [{"date": str(row.date), "interviews": row.count} for row in trend_res.all()]
            
    return {
        "total_users": total_users or 0,
        "total_interviews": total_interviews or 0,
        "total_minutes": round(total_minutes, 1),
        "categories": categories,
        "growth": growth
    }


@router.get("/users")
async def get_admin_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    query = select(
        UserProfileReplica, 
        func.count(InterviewSession.id).label("session_count")
    ).outerjoin(
        InterviewSession, UserProfileReplica.id == InterviewSession.user_id
    ).group_by(UserProfileReplica.id)

    if search:
        search_pat = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(UserProfileReplica.username).like(search_pat),
                func.lower(UserProfileReplica.email).like(search_pat),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = max(0, (page - 1) * limit)
    paginated_query = query.order_by(desc("session_count")).offset(offset).limit(limit)
    result = await db.execute(paginated_query)
    users_with_counts = result.all()
    
    users = []
    for user_obj, session_count in users_with_counts:
        users.append({
            "id": user_obj.id,
            "username": user_obj.username,
            "email": user_obj.email,
            "total_interviews": session_count
        })
        
    pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "items": users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@router.get("/interviews")
async def get_admin_interviews(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    interview_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    query = select(InterviewSession).options(
        joinedload(InterviewSession.feedback),
        joinedload(InterviewSession.user)
    )

    if interview_type:
        query = query.where(func.lower(InterviewSession.interview_type) == interview_type.lower())
    if status:
        query = query.where(func.lower(InterviewSession.stage) == status.lower())
    if search:
        search_pat = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(InterviewSession.candidate_name).like(search_pat),
                func.lower(InterviewSession.id).like(search_pat),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = max(0, (page - 1) * limit)
    paginated_query = query.order_by(desc(InterviewSession.created_at)).offset(offset).limit(limit)
    result = await db.execute(paginated_query)
    sessions = result.scalars().all()
    
    interviews = []
    for session in sessions:
        duration_mins = 0
        if session.created_at and session.updated_at and session.stage == 'completed':
            duration_mins = (session.updated_at - session.created_at).total_seconds() / 60.0
            
        score = None
        if session.feedback:
            score = round((session.feedback.technical_score + session.feedback.communication_score) / 2)
            
        interviews.append({
            "id": session.id,
            "user_email": session.user.email if session.user else "Unknown",
            "candidate_name": session.candidate_name,
            "type": session.interview_type,
            "stage": session.stage,
            "duration_minutes": round(duration_mins, 1),
            "score": score,
            "created_at": session.created_at.isoformat() if session.created_at else None
        })
        
    pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "items": interviews,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@router.get("/interviews/{session_id}")
async def get_admin_interview_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    stmt = (
        select(InterviewSession)
        .options(
            joinedload(InterviewSession.feedback),
            joinedload(InterviewSession.messages),
            joinedload(InterviewSession.user)
        )
        .where(InterviewSession.id == session_id)
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    messages = sorted(session.messages, key=lambda m: m.created_at) if session.messages else []
    transcript = [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]

    feedback_data = None
    if session.feedback:
        f = session.feedback
        feedback_data = {
            "technical_score": f.technical_score,
            "communication_score": f.communication_score,
            "english_score": f.english_score,
            "strengths": json.loads(f.strengths) if isinstance(f.strengths, str) else (f.strengths or []),
            "weaknesses": json.loads(f.weaknesses) if isinstance(f.weaknesses, str) else (f.weaknesses or []),
            "improvement_plan": json.loads(f.improvement_plan) if isinstance(f.improvement_plan, str) else (f.improvement_plan or []),
            "recommended_topics": f.recommended_topics or [],
            "detailed_metrics": f.detailed_metrics or {}
        }

    return {
        "id": session.id,
        "candidate_name": session.candidate_name,
        "interview_type": session.interview_type,
        "stage": session.stage,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "user": {
            "id": session.user.id,
            "email": session.user.email,
            "username": session.user.username,
        } if session.user else None,
        "feedback": feedback_data,
        "transcript": transcript
    }


@router.patch("/interviews/{session_id}/score")
async def override_interview_score_admin(
    session_id: str,
    payload: ScoreOverrideRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    stmt = select(InterviewFeedback).where(InterviewFeedback.session_id == session_id)
    result = await db.execute(stmt)
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Interview feedback not found for this session")

    if payload.technical_score is not None:
        feedback.technical_score = payload.technical_score
    if payload.communication_score is not None:
        feedback.communication_score = payload.communication_score
    if payload.english_score is not None:
        feedback.english_score = payload.english_score

    await db.commit()
    await db.refresh(feedback)

    return {
        "message": "Interview score overridden successfully",
        "session_id": session_id,
        "technical_score": feedback.technical_score,
        "communication_score": feedback.communication_score,
        "english_score": feedback.english_score
    }


@router.delete("/interviews/{session_id}")
async def delete_interview_session_admin(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    stmt = select(InterviewSession).where(InterviewSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    await db.delete(session)
    await db.commit()

    return {"message": "Interview session deleted successfully", "session_id": session_id}
