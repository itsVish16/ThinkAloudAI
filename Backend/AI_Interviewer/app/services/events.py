import json
import logging
import os
import aio_pika
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger("event_publisher")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    health_check_interval=10,
    retry_on_timeout=True,
    socket_timeout=5,
    socket_connect_timeout=5
)

async def publish_interview_completed(
    session_id: str, 
    user_id: str,
    candidate_name: str,
    domain: str, 
    overall_score: int,
    interview_type: str = "Behavioral",
    difficulty: str | None = None,
    technical_score: int | None = None,
    communication_score: int | None = None,
    english_score: int | None = None,
):
    """
    Publishes the InterviewCompleted event to the RabbitMQ Event Bus.
    The User Service consumes this to update user_stats, user_skill_scores, and daily_activity.
    """
    try:
        # overall_score is passed in arguments
            
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
        
        # Publish to Redis for real-time SSE frontend updates
        await redis_client.publish("interview_events", json.dumps(event_data))
        
        # Publish to RabbitMQ for rock-solid cross-service data aggregation
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange("interview_events_exchange", aio_pika.ExchangeType.FANOUT, durable=True)
            message = aio_pika.Message(
                body=json.dumps(event_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await exchange.publish(message, routing_key="interview_events")
            
        # Update Leaderboard
        try:
            await redis_client.zincrby("global_leaderboard", overall_score, candidate_name)
        except Exception as lb_err:
            logger.error(f"Failed to update leaderboard: {lb_err}")
        
        logger.info(f"Successfully published InterviewCompleted for session {session_id} to Redis and RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to publish InterviewCompleted event: {e}")
