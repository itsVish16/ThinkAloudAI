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
    Injects Datadog distributed trace headers for cross-service APM visibility.
    """
    event_payload = {
        "event": "InterviewCompleted",
        "data": {
            "interview_id": session_id,
            "user_id": user_id,
            "score": overall_score,
            "type": interview_type,
            "domain": domain,
            "technical_score": technical_score,
            "communication_score": communication_score,
            "english_score": english_score,
            "feedback": feedback_text or "",
            "detailed_metrics": detailed_metrics or {},
        },
    }

    # Tag active span with domain metadata if Datadog is present
    try:
        from ddtrace import tracer
        root_span = tracer.current_root_span()
        if root_span:
            root_span.set_tag("usr.id", user_id)
            root_span.set_tag("interview.session_id", session_id)
            root_span.set_tag("interview.type", interview_type)
            root_span.set_tag("interview.score", overall_score)
    except Exception:
        pass

    # Publish to Redis for real-time SSE frontend updates
    try:
        await redis_client.publish("interview_events", json.dumps(event_payload))
    except Exception as redis_err:
        logger.error(f"Failed to publish to Redis: {redis_err}")

    # Inject Datadog trace context into RabbitMQ headers
    headers: Dict[str, Any] = {}
    try:
        from ddtrace import tracer
        current_span = tracer.current_span()
        if current_span:
            tracer.inject(current_span.context, headers)
    except Exception:
        pass

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
                headers=headers,
            )
            await exchange.publish(message, routing_key="interview.completed")
    except Exception as rmq_err:
        logger.error(f"Failed to publish to RabbitMQ: {rmq_err}")

    # Update Leaderboard in Redis (Track highest score per candidate)
    try:
        member = f"{user_id}:{candidate_name}"
        current_lb_score = await redis_client.zscore("global_leaderboard", member)
        if current_lb_score is None or overall_score > float(current_lb_score):
            await redis_client.zadd("global_leaderboard", {member: overall_score})
    except Exception as lb_err:
        logger.error(f"Failed to update leaderboard: {lb_err}")

    logger.info(f"Successfully published InterviewCompleted for session {session_id}")
    return event_payload
