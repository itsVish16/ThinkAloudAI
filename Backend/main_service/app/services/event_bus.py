import json
import logging
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize a global Redis connection pool with health checks for Upstash
redis_client = redis.from_url(
    settings.UPSTASH_REDIS_URL, 
    decode_responses=True,
    health_check_interval=10,
    retry_on_timeout=True,
    socket_timeout=5,
    socket_connect_timeout=5
)

async def publish_event(topic: str, payload: dict):
    """
    Publish an event to the Upstash Redis Event Bus.
    """
    try:
        message = json.dumps(payload)
        await redis_client.publish(topic, message)
        logger.info(f"Published event '{topic}' to Redis.")
    except Exception as e:
        logger.error(f"Failed to publish event '{topic}': {e}")
