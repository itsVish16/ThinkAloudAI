import json
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import sqlalchemy.exc

from app.config import settings
from app.models.base import Base
from app.models.interview import UserProfileReplica, InterviewSession, InterviewQuestion, InterviewResponse, InterviewFeedback

import re
from urllib.parse import quote_plus, unquote_plus

def get_normalized_db_url(raw_url: str) -> str:
    if not raw_url:
        return "postgresql+asyncpg://thinkaloud:thinkaloud_dev@localhost:5432/postgres"
    url = raw_url.strip()
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    if "sslmode=require" in url and "ssl=" not in url:
        url = url.replace("sslmode=require", "ssl=require")

    match = re.match(r"^(postgresql\+asyncpg://)(.*)@([^@/]+(?::\d+)?(?:/.*)?)$", url)
    if match:
        proto, creds, rest = match.groups()
        if ":" in creds:
            u, p = creds.split(":", 1)
            encoded_u = quote_plus(unquote_plus(u))
            encoded_p = quote_plus(unquote_plus(p))
            return f"{proto}{encoded_u}:{encoded_p}@{rest}"

    return url

# Database configuration
DATABASE_URL = get_normalized_db_url(settings.DATABASE_URL)
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

import asyncio
import asyncpg
from urllib.parse import urlparse
from sqlalchemy import text

async def ensure_db_exists(db_url: str):
    if not db_url or "sqlite" in db_url:
        return
    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://")
    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip("/")
    if "?" in db_name:
        db_name = db_name.split("?")[0]
    user = unquote_plus(parsed.username or "thinkaloud")
    password = unquote_plus(parsed.password or "thinkaloud_prod_secure")
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    use_ssl = "ssl=" in db_url or "sslmode=" in db_url or "azure.com" in host

    if db_name.lower() == "postgres":
        return

    for attempt in range(1, 4):
        try:
            connect_kwargs = {
                "user": user,
                "password": password,
                "host": host,
                "port": port,
                "database": "postgres",
                "timeout": 5,
            }
            if use_ssl:
                connect_kwargs["ssl"] = "require"

            conn = await asyncpg.connect(**connect_kwargs)
            try:
                exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
                if not exists:
                    await conn.execute(f'CREATE DATABASE "{db_name}"')
            finally:
                await conn.close()
            return
        except Exception:
            await asyncio.sleep(1)


async def init_db():
    try:
        await ensure_db_exists(settings.DATABASE_URL)
    except Exception:
        pass

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Add missing columns dynamically
        await conn.execute(text("ALTER TABLE interview_feedback ADD COLUMN IF NOT EXISTS detailed_metrics JSON;"))

from sqlalchemy.dialects.postgresql import insert as pg_insert

async def get_or_create_user_replica(session: AsyncSession, user_id: str, email: str = None, username: str = None):
    safe_email = email if email else "unknown@thinkaloudai.tech"
    stmt = (
        pg_insert(UserProfileReplica)
        .values(id=str(user_id), email=safe_email, username=username)
        .on_conflict_do_update(
            index_elements=["id"],
            set_={
                "email": safe_email if email else UserProfileReplica.email,
                "username": username if username else UserProfileReplica.username,
            },
        )
        .returning(UserProfileReplica)
    )
    result = await session.execute(stmt)
    await session.flush()
    return result.scalar_one_or_none()

async def save_interview_session(
    session_id: str,
    user_id: str,
    candidate_name: str,
    interview_type: str,
    stage: str,
    state_data: Dict[str, Any],
    resume_summary: Optional[str] = None,
    email: Optional[str] = "unknown@thinkaloudai.tech"
):
    async with AsyncSessionLocal() as session:
        # Ensure user replica exists
        await get_or_create_user_replica(session, user_id, email=email, username=candidate_name)
        
        # Extract difficulty dynamically from state_data if available, otherwise default to Medium
        difficulty = "Medium"
        if state_data and isinstance(state_data, dict):
            questions = state_data.get("ai_selected_questions", [])
            if questions and isinstance(questions, list) and len(questions) > 0:
                q_diff = questions[0].get("difficulty")
                if q_diff:
                    difficulty = str(q_diff).capitalize()
        
        now = datetime.now(UTC).replace(tzinfo=None)
        stmt = pg_insert(InterviewSession).values(
            id=session_id,
            user_id=user_id,
            candidate_name=candidate_name,
            interview_type=interview_type,
            stage=stage,
            state_data=state_data,
            difficulty=difficulty,
            created_at=now,
            updated_at=now
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['id'],
            set_={
                'stage': stage,
                'state_data': state_data,
                'difficulty': difficulty,
                'updated_at': now
            }
        )
        
        await session.execute(stmt)
        await session.commit()

def compute_domain_weighted_score(interview_type: Optional[str], tech: Optional[float], comm: Optional[float], eng: Optional[float], detailed_metrics: Optional[Dict[str, Any]] = None) -> int:
    if detailed_metrics and isinstance(detailed_metrics, dict) and detailed_metrics.get("overall_score") is not None:
        try:
            return round(float(detailed_metrics["overall_score"]))
        except (ValueError, TypeError):
            pass

    t = tech or 0
    c = comm or 0
    e = eng or 0
    i_type_clean = (interview_type or "").lower()
    if any(k in i_type_clean for k in ["dsa", "swe", "coding"]):
        return round(0.60 * t + 0.25 * c + 0.15 * e)
    elif any(k in i_type_clean for k in ["system_design", "sd"]):
        return round(0.55 * t + 0.30 * c + 0.15 * e)
    elif any(k in i_type_clean for k in ["behavioral", "hr"]):
        return round(0.20 * t + 0.70 * c + 0.10 * e)
    elif any(k in i_type_clean for k in ["pm", "product"]):
        return round(0.55 * t + 0.35 * c + 0.10 * e)
    elif any(k in i_type_clean for k in ["ai", "ml"]):
        return round(0.60 * t + 0.25 * c + 0.15 * e)
    else:
        return round(0.40 * t + 0.40 * c + 0.20 * e)

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

            det_metrics = getattr(interview.feedback, "detailed_metrics", None)
            overall_score = compute_domain_weighted_score(
                interview.interview_type,
                interview.feedback.technical_score,
                interview.feedback.communication_score,
                interview.feedback.english_score,
                det_metrics
            )

            feedback_data = {
                "technical_score": interview.feedback.technical_score,
                "communication_score": interview.feedback.communication_score,
                "english_score": interview.feedback.english_score,
                "overall_score": overall_score,
                "strengths": safe_json_load(interview.feedback.strengths),
                "weaknesses": safe_json_load(interview.feedback.weaknesses),
                "improvement_plan": safe_json_load(interview.feedback.improvement_plan),
                "recommended_topics": interview.feedback.recommended_topics,
                "detailed_metrics": det_metrics
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
                det_metrics = getattr(interview.feedback, "detailed_metrics", None)
                overall_score = compute_domain_weighted_score(
                    interview.interview_type,
                    interview.feedback.technical_score,
                    interview.feedback.communication_score,
                    interview.feedback.english_score,
                    det_metrics
                )
                feedback_data = {
                    "technical_score": interview.feedback.technical_score,
                    "communication_score": interview.feedback.communication_score,
                    "english_score": interview.feedback.english_score,
                    "overall_score": overall_score,
                    "detailed_metrics": det_metrics
                }
            ai_selected_questions = []
            if interview.state_data and isinstance(interview.state_data, dict):
                ai_selected_questions = interview.state_data.get("ai_selected_questions", [])
            
            output.append({
                "id": interview.id,
                "interview_type": interview.interview_type,
                "difficulty": interview.difficulty,
                "stage": interview.stage,
                "ai_selected_questions": ai_selected_questions,
                "feedback": feedback_data,
                "created_at": interview.created_at.isoformat() if interview.created_at else None,
                "updated_at": interview.updated_at.isoformat() if interview.updated_at else None
            })
        return output

async def get_user_analytics(user_id: str) -> Dict[str, Any]:
    async with AsyncSessionLocal() as session:
        # Fetch all completed interviews with feedback for this user
        stmt = (
            select(InterviewSession)
            .options(joinedload(InterviewSession.feedback))
            .where(InterviewSession.user_id == user_id)
            .where(InterviewSession.stage == "completed")
            .order_by(InterviewSession.created_at.asc())
        )
        result = await session.execute(stmt)
        sessions = result.scalars().unique().all()
        
        trends = []
        categories = {}
        weekly = [0] * 7 # M, T, W, T, F, S, S
        
        # Monthly grouping for trends
        month_scores = {} # "YYYY-MM": []
        
        # Radar dimensions
        tech_scores = []
        comm_scores = []
        eng_scores = []
        
        for s in sessions:
            if not s.feedback:
                continue
            
            # Calculate overall score for this session
            fb = s.feedback
            scores_list = [v for v in [fb.technical_score, fb.communication_score, fb.english_score] if v is not None and v > 0]
            if not scores_list:
                continue
            score = sum(scores_list) // len(scores_list)
            
            # Monthly trends
            if s.created_at:
                month_key = s.created_at.strftime("%b") # e.g. "Jan", "Feb"
                month_scores.setdefault(month_key, []).append(score)
                
                # Weekly activity (0-6 index where 0 is Monday)
                day_idx = s.created_at.weekday()
                weekly[day_idx] += 1
            
            # Category average
            cat = s.interview_type or "Behavioral"
            categories.setdefault(cat, []).append(score)
            
            if fb.technical_score is not None and fb.technical_score > 0:
                tech_scores.append(fb.technical_score)
            if fb.communication_score is not None and fb.communication_score > 0:
                comm_scores.append(fb.communication_score)
            if fb.english_score is not None and fb.english_score > 0:
                eng_scores.append(fb.english_score)

        # Format trendsData
        trends_data = []
        for m, scs in month_scores.items():
            trends_data.append({
                "month": m,
                "score": sum(scs) // len(scs)
            })
            
        # Format categoryData
        category_data = []
        for cat, scs in categories.items():
            category_data.append({
                "category": cat,
                "score": sum(scs) // len(scs)
            })
            
        # Format weeklyData
        day_names = ["M", "T", "W", "T", "F", "S", "S"]
        weekly_data = []
        for i, val in enumerate(weekly):
            weekly_data.append({
                "day": day_names[i],
                "count": val
            })
            
        # Format radarData
        radar_data = [
            {"subject": "Technical", "A": sum(tech_scores) // len(tech_scores) if tech_scores else 0, "fullMark": 100},
            {"subject": "Communication", "A": sum(comm_scores) // len(comm_scores) if comm_scores else 0, "fullMark": 100},
            {"subject": "English", "A": sum(eng_scores) // len(eng_scores) if eng_scores else 0, "fullMark": 100},
        ]
        
        return {
            "trendsData": trends_data,
            "categoryData": category_data,
            "weeklyData": weekly_data,
            "radarData": radar_data
        }
