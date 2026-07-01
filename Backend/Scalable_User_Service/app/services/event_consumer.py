import asyncio
import contextlib
import json
from datetime import UTC, datetime, date, timedelta

import structlog
from ddtrace import tracer
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.db.redis import get_redis
from app.models.learning import LearningEvent, UserStats, DailyActivity, UserSkillScore

logger = structlog.get_logger(__name__)

MAIN_EVENTS_CHANNEL = "main_events"
INTERVIEW_EVENTS_CHANNEL = "interview_events"

async def _invalidate_profile_cache(user_id: int):
    try:
        redis: Redis = await get_redis()
        cache_key = f"user:full_profile:{user_id}"
        await redis.delete(cache_key)
    except Exception as e:
        logger.error("failed_to_invalidate_cache", user_id=user_id, error=str(e))

async def _upsert_stats(db, user_id: int, difficulty: str = None, is_interview: bool = False, interview_score: int = 0):
    while True:
        res = await db.execute(select(UserStats).filter_by(user_id=user_id).with_for_update())
        stats = res.scalar_one_or_none()
        if not stats:
            stats = UserStats(user_id=user_id)
            db.add(stats)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                continue
        
        if not is_interview:
            stats.total_submissions += 1
            if difficulty:
                stats.problems_solved_total += 1
                if difficulty.lower() == "easy":
                    stats.problems_solved_easy += 1
                elif difficulty.lower() == "medium":
                    stats.problems_solved_medium += 1
                elif difficulty.lower() == "hard":
                    stats.problems_solved_hard += 1
                
            stats.acceptance_rate = (stats.problems_solved_total / stats.total_submissions) * 100.0 if stats.total_submissions > 0 else 0.0
        else:
            stats.interviews_completed += 1
            total_score = (stats.avg_interview_score * (stats.interviews_completed - 1)) + interview_score
            stats.avg_interview_score = total_score / stats.interviews_completed
            if interview_score > stats.best_interview_score:
                stats.best_interview_score = interview_score
                
        # Streak logic
        today = datetime.now(UTC).date()
        if stats.last_activity_date != today:
            # Continue streak only if the last activity was exactly yesterday
            # (timezone-safe; avoids the old broken month-boundary arithmetic)
            if stats.last_activity_date == today - timedelta(days=1):
                stats.current_streak += 1
            else:
                stats.current_streak = 1
            if stats.current_streak > stats.longest_streak:
                stats.longest_streak = stats.current_streak
            stats.last_activity_date = today

        # Basic rating
        stats.rating = (stats.problems_solved_total * 10) + (stats.interviews_completed * 50) + int(stats.avg_interview_score)

        return stats

async def _upsert_daily_activity(db, user_id: int, is_problem_solved: bool = False, is_interview: bool = False):
    today = datetime.now(UTC).date()
    while True:
        res = await db.execute(select(DailyActivity).filter_by(user_id=user_id, activity_date=today).with_for_update())
        activity = res.scalar_one_or_none()
        if not activity:
            activity = DailyActivity(user_id=user_id, activity_date=today)
            db.add(activity)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                continue
        
        if is_problem_solved:
            activity.problems_solved += 1
            activity.problems_attempted += 1 # Rough approximation
            activity.submissions_count += 1
        elif not is_interview:
            activity.submissions_count += 1
            
        if is_interview:
            activity.interviews_done += 1
            
        return activity

async def _upsert_skill(db, user_id: int, domain: str, score_inc: int, is_problem_solved: bool = False, is_interview: bool = False):
    while True:
        result = await db.execute(select(UserSkillScore).filter_by(user_id=user_id, domain=domain).with_for_update())
        skill = result.scalar_one_or_none()

        if not skill:
            skill = UserSkillScore(user_id=user_id, domain=domain, score=0)
            db.add(skill)
            try:
                await db.flush()
            except IntegrityError:
                await db.rollback()
                continue

        skill.score += score_inc
        if is_problem_solved:
            skill.problems_solved += 1
        if is_interview:
            skill.interviews_done += 1
            
        return skill

@tracer.wrap(service="user-service", resource="handle_problem_solved")
async def handle_problem_solved(data: dict):
    """Handles the ProblemSolved event from the Main Service."""
    user_id = data.get("user_id")
    problem_id = data.get("problem_id")
    language = data.get("language", "unknown")
    difficulty = data.get("difficulty", "easy")
    score_change = data.get("score_change", 10)

    if not user_id:
        return

    async with SessionLocal() as db:
        await _upsert_stats(db, user_id, difficulty=difficulty)
        await _upsert_daily_activity(db, user_id, is_problem_solved=True)
        await _upsert_skill(db, user_id, language, score_change, is_problem_solved=True)

        # Log the learning event
        event = LearningEvent(
            user_id=user_id,
            event_type="ProblemSolved",
            reference_id=str(problem_id) if problem_id else None,
            score_change=score_change,
            domain=language,
            metadata_json={"difficulty": difficulty, "language": language}
        )
        db.add(event)

        await db.commit()
        await _invalidate_profile_cache(user_id)
        logger.info("processed_problem_solved", user_id=user_id, language=language)


@tracer.wrap(service="user-service", resource="handle_interview_completed")
async def handle_interview_completed(data: dict):
    """Handles the InterviewCompleted event from the Interview Service."""
    user_id = data.get("user_id")
    interview_id = data.get("interview_id")
    domain = data.get("domain", "general")
    overall_score = data.get("overall_score", 0)

    if not user_id:
        return

    async with SessionLocal() as db:
        await _upsert_stats(db, user_id, is_interview=True, interview_score=overall_score)
        await _upsert_daily_activity(db, user_id, is_interview=True)
        await _upsert_skill(db, user_id, domain, overall_score, is_interview=True)

        event = LearningEvent(
            user_id=user_id,
            event_type="InterviewCompleted",
            reference_id=str(interview_id) if interview_id else None,
            score_change=overall_score,
            domain=domain,
            metadata_json={"score": overall_score}
        )
        db.add(event)

        await db.commit()
        await _invalidate_profile_cache(user_id)
        logger.info("processed_interview_completed", user_id=user_id, domain=domain)


async def event_consumer_loop():
    """Background task that continuously listens to Redis Pub/Sub with infinite retry."""
    logger.info("event_consumer_starting", channels=[MAIN_EVENTS_CHANNEL, INTERVIEW_EVENTS_CHANNEL])

    retry_delay = 1
    max_delay = 60

    while True:
        try:
            redis: Redis = await get_redis()
            pubsub = redis.pubsub()
            
            try:
                await pubsub.subscribe(MAIN_EVENTS_CHANNEL, INTERVIEW_EVENTS_CHANNEL)
                logger.info("event_consumer_connected")
    
                retry_delay = 1
    
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            payload = json.loads(message["data"])
                            event_type = payload.get("event")
                            data = payload.get("data", {})
    
                            if event_type == "ProblemSolved":
                                await handle_problem_solved(data)
                            elif event_type == "InterviewCompleted":
                                await handle_interview_completed(data)
                            else:
                                logger.debug("ignored_unknown_event", event_type=event_type)
    
                        except Exception as e:
                            logger.error("error_processing_event", error=str(e), message=message)
            finally:
                with contextlib.suppress(Exception):
                    await pubsub.close()
                    
        except asyncio.CancelledError:
            logger.info("event_consumer_stopped")
            break
        except Exception as e:
            logger.error("event_consumer_connection_lost", error=str(e), retrying_in=retry_delay)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)

