import json
import logging
import os
import aio_pika
from typing import Optional

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

_connection: Optional[aio_pika.Connection] = None
_channel: Optional[aio_pika.Channel] = None
_exchange: Optional[aio_pika.Exchange] = None

async def get_rabbitmq_exchange() -> aio_pika.Exchange:
    global _connection, _channel, _exchange
    
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
        
    if _channel is None or _channel.is_closed:
        _channel = await _connection.channel()
        # Create a fanout exchange for pub/sub events
        _exchange = await _channel.declare_exchange(
            "main_events_exchange", 
            aio_pika.ExchangeType.FANOUT, 
            durable=True
        )
        
    return _exchange

async def publish_event(topic: str, payload: dict):
    """
    Publish an event to the RabbitMQ Event Bus.
    Note: Since we use FANOUT, all bound queues will receive it, but we can also use topic exchange.
    For simplicity and backward compatibility with "main_events" topic, we use fanout.
    """
    try:
        exchange = await get_rabbitmq_exchange()
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await exchange.publish(message, routing_key=topic)
        logger.info(f"Published event '{topic}' to RabbitMQ.")
    except Exception as e:
        logger.error(f"Failed to publish event '{topic}' to RabbitMQ: {e}")
