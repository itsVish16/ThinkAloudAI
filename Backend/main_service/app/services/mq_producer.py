import json
import logging
from typing import Dict, Any
from aio_pika import connect_robust, Message, DeliveryMode
from app.config import settings

logger = logging.getLogger(__name__)

_rabbitmq_connection = None

async def get_mq_connection():
    global _rabbitmq_connection
    if _rabbitmq_connection is None or _rabbitmq_connection.is_closed:
        url = settings.RABBITMQ_URL if hasattr(settings, 'RABBITMQ_URL') else "amqp://guest:guest@localhost:5672/"
        _rabbitmq_connection = await connect_robust(url)
    return _rabbitmq_connection

async def publish_execution_task(task_data: dict):
    """
    Publishes a code execution task to RabbitMQ with Datadog trace context propagation.
    """
    try:
        connection = await get_mq_connection()
        channel = await connection.channel()
        queue = await channel.declare_queue("code_execution_queue", durable=True)
        
        headers: Dict[str, Any] = {}
        try:
            from ddtrace import tracer
            current_span = tracer.current_span()
            if current_span:
                tracer.inject(current_span.context, headers)
        except Exception:
            pass

        await channel.default_exchange.publish(
            Message(
                body=json.dumps(task_data).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                headers=headers,
            ),
            routing_key="code_execution_queue"
        )
        await channel.close()
    except Exception as e:
        logger.error(f"Failed to publish execution task: {e}")
        raise
