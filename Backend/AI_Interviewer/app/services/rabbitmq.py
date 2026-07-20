import json
import logging
import os
import aio_pika
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global connection to reuse
_connection: Optional[aio_pika.Connection] = None
_channel: Optional[aio_pika.Channel] = None

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

async def get_rabbitmq_channel() -> aio_pika.Channel:
    """
    Get or create a global RabbitMQ channel.
    """
    global _connection, _channel
    
    if _connection is None or _connection.is_closed:
        logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}")
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
        
    if _channel is None or _channel.is_closed:
        _channel = await _connection.channel()
        # Declare the queues we need right away to ensure they exist
        await _channel.declare_queue("interview_analysis_queue", durable=True)
        
    return _channel

async def publish_analysis_task(payload: Dict[str, Any]):
    """
    Publish an analysis task to the interview_analysis_queue.
    """
    try:
        channel = await get_rabbitmq_channel()
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await channel.default_exchange.publish(
            message,
            routing_key="interview_analysis_queue"
        )
        logger.info(f"Published analysis task for session {payload.get('session_id')} to RabbitMQ.")
    except Exception as e:
        logger.error(f"Failed to publish analysis task to RabbitMQ: {e}")
        # Depending on criticality, we might want to re-raise or handle the exception
