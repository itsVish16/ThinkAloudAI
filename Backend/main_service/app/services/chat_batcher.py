import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import SessionLocal, get_redis
from app.models.chat import ChatMessageModel
from app.config import settings

logger = logging.getLogger(__name__)

CHAT_BUFFER_KEY = "chat:buffer"
BATCH_SIZE = 50
FLUSH_INTERVAL = 5.0  # seconds

async def flush_chat_buffer():
    """Reads messages from Redis buffer and bulk inserts them into PostgreSQL."""
    try:
        from app.database import redis_client as redis
        raw_msgs = await redis.lrange(CHAT_BUFFER_KEY, 0, BATCH_SIZE - 1)
        if not raw_msgs:
            return

        messages = []
        for raw in raw_msgs:
            try:
                messages.append(json.loads(raw))
            except json.JSONDecodeError:
                logger.error("Failed to decode message from Redis buffer")
        
        if messages:
            logger.info(f"Flushing {len(messages)} chat messages to DB")
            async with SessionLocal() as db:
                db_messages = []
                for msg_data in messages:
                    db_messages.append(
                        ChatMessageModel(
                            session_id=msg_data["session_id"],
                            role=msg_data["role"],
                            content=msg_data["content"],
                        )
                    )
                db.add_all(db_messages)
                await db.commit()
                
        # If DB commit is successful (or there were only invalid messages), trim from Redis
        await redis.ltrim(CHAT_BUFFER_KEY, len(raw_msgs), -1)

    except Exception as e:
        logger.error(f"Error flushing chat buffer: {e}")

async def start_chat_batch_writer():
    """Background task loop that flushes the Redis chat buffer periodically."""
    logger.info("Starting chat batch writer background task...")
    while True:
        try:
            await flush_chat_buffer()
        except Exception as e:
            logger.error(f"Unexpected error in chat batch writer loop: {e}")
        await asyncio.sleep(FLUSH_INTERVAL)
