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
    Enqueues and processes an email sending job immediately with Redis fallback.
    """
    logger.info("dispatching_email_task", task_type=task_type, email=email)
    try:
        await process_email(task_type, email, payload)
    except Exception as err:
        logger.error("direct_email_send_error", error=str(err), task_type=task_type, email=email)
        try:
            redis: Redis = await get_redis()
            task = {
                "type": task_type,
                "email": email,
                "payload": payload,
            }
            await redis.rpush(EMAIL_QUEUE_KEY, json.dumps(task))
            logger.info("email_task_requeued_to_redis", task_type=task_type, email=email)
        except Exception as queue_err:
            logger.error("redis_requeue_failed", error=str(queue_err), task_type=task_type, email=email)


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
