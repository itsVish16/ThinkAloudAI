import asyncio
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import SessionLocal, redis_client
from sqlalchemy.future import select
from app.models.chat import ChatSession, ChatMessageModel
from app.config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 50
FLUSH_INTERVAL = 5.0  # seconds

# Lua script to atomically read and pop up to N elements from the head of the list
LUA_POP_BATCH = """
local key = KEYS[1]
local count = tonumber(ARGV[1])
local items = redis.call('LRANGE', key, 0, count - 1)
if #items > 0 then
    redis.call('LTRIM', key, #items, -1)
end
return items
"""

async def flush_session_buffer(redis, session_key: str):
    """
    Atomically pops a batch of messages from a session-specific buffer
    and writes them to PostgreSQL. Requeues messages if DB write fails.
    """
    try:
        raw_msgs = await redis.eval(LUA_POP_BATCH, 1, session_key, BATCH_SIZE)
        if not raw_msgs:
            return

        messages = []
        for raw in raw_msgs:
            try:
                messages.append(json.loads(raw))
            except json.JSONDecodeError:
                logger.error(f"Failed to decode message from buffer {session_key}")

        if messages:
            try:
                async with SessionLocal() as db:
                    # First verify or create parent ChatSession records to prevent FK violations
                    session_ids = {m["session_id"] for m in messages if "session_id" in m}
                    for s_id in session_ids:
                        res = await db.execute(select(ChatSession).filter(ChatSession.id == s_id))
                        if not res.scalars().first():
                            db.add(ChatSession(id=s_id))
                    await db.flush()

                    db_messages = [
                        ChatMessageModel(
                            session_id=msg_data["session_id"],
                            role=msg_data["role"],
                            content=msg_data["content"],
                        )
                        for msg_data in messages
                    ]
                    db.add_all(db_messages)
                    await db.commit()
                logger.info(f"Flushed {len(messages)} chat messages from {session_key} to DB")
            except Exception as db_err:
                logger.error(f"Failed to write chat batch to DB for {session_key}: {db_err}. Requeuing.")
                try:
                    await redis.lpush(session_key, *reversed(raw_msgs))
                except Exception as re_err:
                    logger.error(f"Failed to requeue messages into {session_key}: {re_err}")
                raise

    except Exception as e:
        logger.error(f"Error flushing session buffer {session_key}: {e}")

async def flush_chat_buffer():
    """Discovers all per-session chat buffers via scan_iter and flushes each atomically."""
    try:
        redis = redis_client
        
        # Drain legacy global buffer if any items exist
        legacy_msgs = await redis.lrange("chat:buffer", 0, -1)
        if legacy_msgs:
            await redis.delete("chat:buffer")
            for raw in legacy_msgs:
                try:
                    data = json.loads(raw)
                    s_id = data.get("session_id")
                    if s_id:
                        await redis.rpush(f"chat:buffer:{s_id}", raw)
                except Exception:
                    pass

        session_keys = []
        async for key in redis.scan_iter("chat:buffer:*"):
            session_keys.append(key)

        for key in session_keys:
            await flush_session_buffer(redis, key)

    except Exception as e:
        logger.error(f"Error flushing chat buffers: {e}")

async def start_chat_batch_writer():
    """Background task loop that flushes per-session Redis chat buffers periodically."""
    logger.info("Starting chat batch writer background task...")
    while True:
        try:
            await flush_chat_buffer()
        except asyncio.CancelledError:
            logger.info("Chat batch writer task cancelled.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in chat batch writer loop: {e}")
        await asyncio.sleep(FLUSH_INTERVAL)
