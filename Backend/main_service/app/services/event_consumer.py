import asyncio
import json
import logging
from aio_pika import connect_robust
from app.config import settings
from app.database import SessionLocal
from sqlalchemy.future import select
from app.models.analytics import UserStats, LearningEvent

logger = logging.getLogger(__name__)

async def process_interview_completed(data: dict):
    """
    Handles the InterviewCompleted event.
    Expected data payload:
    {
        "user_id": "string-uuid",
        "interview_id": "uuid",
        "score": 85.5,
        "type": "System Design",
        "transcript": "...",
        "feedback": "..."
    }
    """
    user_id = data.get("user_id")
    if not user_id:
        logger.error("InterviewCompleted event missing user_id")
        return

    async with SessionLocal() as db:
        # 1. Update User Stats
        stats_res = await db.execute(select(UserStats).filter_by(user_id=user_id))
        stats = stats_res.scalars().first()
        
        if not stats:
            stats = UserStats(user_id=user_id)
            db.add(stats)
            
        stats.interviews_completed += 1
        
        score = data.get("score", 0.0)
        # Update best score
        if score > stats.best_interview_score:
            stats.best_interview_score = int(score)
            
        # Update average score (moving average approximation for simplicity, or recompute)
        if stats.interviews_completed == 1:
            stats.avg_interview_score = score
        else:
            stats.avg_interview_score = (stats.avg_interview_score * (stats.interviews_completed - 1) + score) / stats.interviews_completed

        # 2. Add Learning Event
        event = LearningEvent(
            user_id=user_id,
            event_type="INTERVIEW_COMPLETED",
            reference_id=data.get("interview_id"),
            score_change=score,
            domain=data.get("type", "General"),
            metadata_json={
                "score": score,
                "type": data.get("type")
            }
        )
        db.add(event)
        
        await db.commit()
        logger.info(f"Successfully processed InterviewCompleted for user {user_id}")

async def start_event_consumer():
    """
    Connects to RabbitMQ and listens for events directed at the main service.
    """
    rabbitmq_url = settings.RABBITMQ_URL if hasattr(settings, 'RABBITMQ_URL') else "amqp://guest:guest@localhost:5672/"
    
    while True:
        try:
            connection = await connect_robust(rabbitmq_url)
            channel = await connection.channel()
            
            # Declare exchange and queue
            exchange = await channel.declare_exchange("thinkaloud_events", type="topic", durable=True)
            queue = await channel.declare_queue("main_service_events", durable=True)
            
            # Bind queue to listen for AI Interviewer events
            await queue.bind(exchange, routing_key="interview.completed")
            
            logger.info("Main Service Event Consumer started successfully.")
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            body = json.loads(message.body.decode())
                            event_type = body.get("event")
                            data = body.get("data", {})
                            
                            if event_type == "InterviewCompleted":
                                await process_interview_completed(data)
                            else:
                                logger.info(f"Unhandled event type: {event_type}")
                                
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}. Retrying in 5 seconds...")
            try:
                if 'connection' in locals() and connection and not connection.is_closed:
                    await connection.close()
            except Exception:
                pass
            await asyncio.sleep(5)
