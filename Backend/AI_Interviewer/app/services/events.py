import json
import logging
from typing import Optional, Dict, Any
import aio_pika
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger("event_publisher")

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    health_check_interval=10,
    retry_on_timeout=True,
    socket_timeout=5,
    socket_connect_timeout=5,
)


async def publish_interview_completed(
    session_id: str,
    user_id: str,
    candidate_name: str,
    domain: str,
    overall_score: int,
    interview_type: str = "Behavioral",
    feedback_text: Optional[str] = None,
    detailed_metrics: Optional[Dict[str, Any]] = None,
    difficulty: Optional[str] = None,
    technical_score: Optional[int] = None,
    communication_score: Optional[int] = None,
    english_score: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Publishes the InterviewCompleted event to the RabbitMQ Event Bus and Redis.
    Uses 'thinkaloud_events' topic exchange with routing key 'interview.completed'.
    """
    event_payload = {
        "event": "InterviewCompleted",
        "data": {
            "interview_id": session_id,
            "user_id": user_id,
            "score": overall_score,
            "type": interview_type,
            "domain": domain,
            "feedback": feedback_text or "",
            "detailed_metrics": detailed_metrics or {},
        },
    }

    # Publish to Redis for real-time SSE frontend updates
    try:
        await redis_client.publish("interview_events", json.dumps(event_payload))
    except Exception as redis_err:
        logger.error(f"Failed to publish to Redis: {redis_err}")

    # Publish to RabbitMQ topic exchange 'thinkaloud_events' with routing key 'interview.completed'
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "thinkaloud_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            message = aio_pika.Message(
                body=json.dumps(event_payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await exchange.publish(message, routing_key="interview.completed")
    except Exception as rmq_err:
        logger.error(f"Failed to publish to RabbitMQ: {rmq_err}")

    # Update Leaderboard in Redis
    try:
        await redis_client.zincrby("global_leaderboard", overall_score, candidate_name)
    except Exception as lb_err:
        logger.error(f"Failed to update leaderboard: {lb_err}")

    logger.info(f"Successfully published InterviewCompleted for session {session_id}")
    return event_payload
