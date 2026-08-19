from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
from typing import List, Optional
import os
import httpx

from app.services.db import get_db
from app.models.interview import InterviewSession, UserProfileReplica, InterviewFeedback
from app.services.auth import get_current_user
import logging

logger = logging.getLogger("admin_router")

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def require_admin(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.get("user_id")
    
    # Fetch real email from user-service
    email = current_user.get("email")
    if current_user.get("raw_token"):
        try:
            import os
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

from datetime import datetime, timedelta, UTC

@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db), _: dict = Depends(require_admin)):
    # Total Users
    total_users = await db.scalar(select(func.count(UserProfileReplica.id)))
    
    # Total Interviews
    total_interviews = await db.scalar(select(func.count(InterviewSession.id)))
    
    # Total Interview Minutes (for completed interviews)
    time_stmt = select(
        func.sum(func.extract('epoch', InterviewSession.updated_at - InterviewSession.created_at))
    ).where(InterviewSession.stage == 'completed')
    total_seconds = await db.scalar(time_stmt)
    total_minutes = (total_seconds or 0) / 60.0
    
    # Category breakdown
    cat_stmt = select(
        InterviewSession.interview_type, 
        func.count(InterviewSession.id)
    ).where(InterviewSession.stage == 'completed').group_by(InterviewSession.interview_type)
    cat_res = await db.execute(cat_stmt)
    categories = {row[0] or "Unknown": row[1] for row in cat_res.all()}
            
    # 30-day trends
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
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    # Fetch users and count their sessions
    stmt = select(
        UserProfileReplica, 
        func.count(InterviewSession.id).label("session_count")
    ).outerjoin(
        InterviewSession, UserProfileReplica.id == InterviewSession.user_id
    ).group_by(UserProfileReplica.id).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    users_with_counts = result.all()
    
    users = []
    for user_obj, session_count in users_with_counts:
        users.append({
            "id": user_obj.id,
            "username": user_obj.username,
            "email": user_obj.email,
            "total_interviews": session_count
        })
        
    return {"users": users}

@router.get("/interviews")
async def get_admin_interviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    stmt = select(InterviewSession).options(
        joinedload(InterviewSession.feedback),
        joinedload(InterviewSession.user)
    ).order_by(desc(InterviewSession.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
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
        
    return {"interviews": interviews}
