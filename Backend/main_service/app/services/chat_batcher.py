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
    async for redis in get_redis():
        try:
            messages = []
            while len(messages) < BATCH_SIZE:
                raw_msg = await redis.lpop(CHAT_BUFFER_KEY)
                if not raw_msg:
                    break
                try:
                    messages.append(json.loads(raw_msg))
                except json.JSONDecodeError:
                    logger.error("Failed to decode message from Redis buffer")
            
            if not messages:
                return

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
                
        except Exception as e:
            logger.error(f"Error flushing chat buffer: {e}")
        
        break # get_redis yields once

async def start_chat_batch_writer():
    """Background task loop that flushes the Redis chat buffer periodically."""
    logger.info("Starting chat batch writer background task...")
    while True:
        try:
            await flush_chat_buffer()
        except Exception as e:
            logger.error(f"Unexpected error in chat batch writer loop: {e}")
        await asyncio.sleep(FLUSH_INTERVAL)
