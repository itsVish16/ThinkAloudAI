import json
import asyncio
import structlog
from typing import Optional
from redis.asyncio import Redis

from app.db.redis import get_redis
from app.services.email_service import process_email

logger = structlog.get_logger(__name__)

EMAIL_QUEUE_KEY = "user:email_queue"


async def enqueue_email(task_type: str, email: str, payload: dict) -> None:
    """
    Enqueues an email sending job into Redis queue, with immediate local processing fallback.
    """
    try:
        redis: Redis = await get_redis()
        task = {
            "type": task_type,
            "email": email,
            "payload": payload,
        }
        await redis.rpush(EMAIL_QUEUE_KEY, json.dumps(task))
        logger.info("email_task_enqueued", task_type=task_type, email=email)
    except Exception as e:
        logger.warning("redis_enqueue_failed_processing_directly", error=str(e), task_type=task_type, email=email)
        # Direct execution fallback
        try:
            await process_email(task_type, email, payload)
        except Exception as direct_err:
            logger.error("direct_email_processing_failed", error=str(direct_err), task_type=task_type, email=email)


async def email_worker_loop(stop_event: asyncio.Event) -> None:
    """
    Background worker loop that continuously pops and processes email tasks from Redis.
    """
    logger.info("email_worker_started")
    while not stop_event.is_set():
        try:
            redis: Redis = await get_redis()
            # Non-blocking pop with short timeout
            item = await redis.blpop(EMAIL_QUEUE_KEY, timeout=2)
            if item:
                _, raw_data = item
                task = json.loads(raw_data)
                task_type = task.get("type", "")
                email = task.get("email", "")
                payload = task.get("payload", {})
                
                try:
                    await process_email(task_type, email, payload)
                except Exception as send_err:
                    logger.error("email_worker_send_error", error=str(send_err), task_type=task_type, email=email)
        except asyncio.CancelledError:
            break
        except Exception as e:
            if not stop_event.is_set():
                logger.error("email_worker_loop_error", error=str(e))
                await asyncio.sleep(2)
    logger.info("email_worker_stopped")
