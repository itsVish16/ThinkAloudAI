import json
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.models.base import Base
from app.models.interview import UserProfileReplica, InterviewSession, InterviewQuestion, InterviewResponse, InterviewFeedback

# Database configuration
DATABASE_URL = settings.DATABASE_URL
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def get_or_create_user_replica(session: AsyncSession, user_id: str, email: str = None, username: str = None):
    stmt = select(UserProfileReplica).where(UserProfileReplica.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = UserProfileReplica(id=user_id, email=email, username=username)
        session.add(user)
        await session.flush()
    return user

async def save_interview_session(
    session_id: str, 
    user_id: str, 
    candidate_name: str, 
    interview_type: str,
    stage: str, 
    resume_summary: Optional[str], 
    state_data: Dict[str, Any]
):
    async with AsyncSessionLocal() as session:
        # Ensure user replica exists
        await get_or_create_user_replica(session, user_id, username=candidate_name)
        
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        result = await session.execute(stmt)
        interview = result.scalar_one_or_none()
        
        if not interview:
            interview = InterviewSession(
                id=session_id,
                user_id=user_id,
                candidate_name=candidate_name,
                interview_type=interview_type,
                stage=stage,
                state_data=state_data,
                created_at=datetime.now(UTC).replace(tzinfo=None)
            )
            session.add(interview)
        else:
            interview.stage = stage
            interview.state_data = state_data
            interview.updated_at = datetime.now(UTC).replace(tzinfo=None)
            
        await session.commit()

from sqlalchemy.orm import joinedload

async def get_interview_session(session_id: str) -> Optional[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        stmt = select(InterviewSession).options(joinedload(InterviewSession.feedback)).where(InterviewSession.id == session_id)
        result = await session.execute(stmt)
        interview = result.scalar_one_or_none()
        
        if not interview:
            return None
            
        feedback_data = None
        if interview.feedback:
            import json
            def safe_json_load(val):
                if not val: return []
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    return [val]

            feedback_data = {
                "technical_score": interview.feedback.technical_score,
                "communication_score": interview.feedback.communication_score,
                "english_score": interview.feedback.english_score,
                "strengths": safe_json_load(interview.feedback.strengths),
                "weaknesses": safe_json_load(interview.feedback.weaknesses),
                "improvement_plan": safe_json_load(interview.feedback.improvement_plan),
                "recommended_topics": interview.feedback.recommended_topics
            }
            
        return {
            "id": interview.id,
            "user_id": interview.user_id,
            "candidate_name": interview.candidate_name,
            "interview_type": interview.interview_type,
            "stage": interview.stage,
            "state_data": interview.state_data,
            "feedback": feedback_data,
            "created_at": interview.created_at.isoformat() if interview.created_at else None,
            "updated_at": interview.updated_at.isoformat() if interview.updated_at else None
        }

async def get_all_interviews_for_user(user_id: str) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(InterviewSession)
            .options(joinedload(InterviewSession.feedback))
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.created_at.desc())
        )
        result = await session.execute(stmt)
        interviews = result.scalars().unique().all()
        
        output = []
        for interview in interviews:
            feedback_data = None
            if interview.feedback:
                feedback_data = {
                    "technical_score": interview.feedback.technical_score,
                    "communication_score": interview.feedback.communication_score,
                    "english_score": interview.feedback.english_score,
                }
            output.append({
                "id": interview.id,
                "interview_type": interview.interview_type,
                "difficulty": interview.difficulty,
                "stage": interview.stage,
                "feedback": feedback_data,
                "created_at": interview.created_at.isoformat() if interview.created_at else None,
                "updated_at": interview.updated_at.isoformat() if interview.updated_at else None
            })
        return output
