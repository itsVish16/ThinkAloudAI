import json
import logging
from redis.asyncio import Redis
from app.config import settings

logger = logging.getLogger("event_publisher")

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def publish_interview_completed(
    session_id: str, 
    user_id: str, 
    domain: str, 
    overall_score: int,
    interview_type: str = "Behavioral",
    difficulty: str | None = None,
    technical_score: int | None = None,
    communication_score: int | None = None,
    english_score: int | None = None,
):
    """
    Publishes the InterviewCompleted event to the Redis Event Bus.
    The User Service consumes this to update user_stats, user_skill_scores, and daily_activity.
    """
    event_data = {
        "event": "InterviewCompleted",
        "data": {
            "interview_id": session_id,
            "user_id": user_id,
            "domain": domain,
            "overall_score": overall_score,
            "interview_type": interview_type,
            "difficulty": difficulty,
            "technical_score": technical_score,
            "communication_score": communication_score,
            "english_score": english_score,
        }
    }
    try:
        await redis_client.publish("interview_events", json.dumps(event_data))
        logger.info(f"Successfully published InterviewCompleted for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to publish InterviewCompleted event: {e}")
