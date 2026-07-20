import json
import asyncio
import logging
from app.database import SessionLocal
from app.models.user_replica import UserProfileReplica

logger = logging.getLogger(__name__)

async def start_event_consumer():
    """
    Listen to Redis pub/sub topics and process incoming events.
    """
    logger.info("Started Redis Event Consumer for Main Service. Listening to 'UserCreated', 'UserUpdated'.")

    while True:
        try:
            import redis.asyncio as redis
            from app.config import settings
            local_redis_client = redis.from_url(
                settings.UPSTASH_REDIS_URL,
                decode_responses=True,
                health_check_interval=10,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            pubsub = local_redis_client.pubsub()
            try:
                await pubsub.subscribe("UserCreated", "UserUpdated", "user.created", "user.updated")
                
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            topic = message["channel"]
                            data = json.loads(message["data"])
                            logger.info(f"Received event '{topic}': {data}")
                            
                            async with SessionLocal() as db:
                                if topic in ("UserCreated", "user.created"):
                                    payload = data.get("data", data)
                                    # Upsert the replica
                                    from sqlalchemy.dialects.postgresql import insert as pg_insert
                                    stmt = pg_insert(UserProfileReplica).values(
                                        id=str(payload["id"]),
                                        username=payload.get("username", "unknown"),
                                        email=payload.get("email", "unknown"),
                                        display_name=payload.get("full_name") or payload.get("display_name")
                                    ).on_conflict_do_update(
                                        index_elements=["id"],
                                        set_={
                                            "email": payload.get("email", "unknown"),
                                            "username": payload.get("username", "unknown"),
                                            "display_name": payload.get("full_name") or payload.get("display_name")
                                        }
                                    )
                                    await db.execute(stmt)
                                    await db.commit()
                                    logger.info(f"Upserted UserReplica {payload['id']}")

                                elif topic in ("UserUpdated", "user.updated"):
                                    payload = data.get("data", data)
                                    from sqlalchemy.future import select as sa_select
                                    result = await db.execute(
                                        sa_select(UserProfileReplica).filter(UserProfileReplica.id == str(payload["id"]))
                                    )
                                    replica = result.scalars().first()
                                    if replica:
                                        replica.username = payload.get("username", replica.username)
                                        replica.email = payload.get("email", replica.email)
                                        replica.display_name = payload.get("full_name") or payload.get("display_name", replica.display_name)
                                        await db.commit()
                                        logger.info(f"Updated UserReplica {payload['id']}")
                        except Exception as e:
                            logger.error(f"Error processing event: {e}")
            finally:
                import contextlib
                with contextlib.suppress(Exception):
                    await pubsub.close()
        except asyncio.CancelledError:
            logger.info("Event Consumer stopped.")
            break
        except Exception as e:
            logger.error(f"Event Consumer crashed, reconnecting in 5s... Error: {e}")
            await asyncio.sleep(5)
