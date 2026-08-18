import asyncio
import json
import logging
from aio_pika import connect_robust
from app.config import settings
from app.database import SessionLocal
from sqlalchemy.future import select
from app.models.analytics import UserStats, LearningEvent, UserSkillScore

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
        "domain": "system_design",
        "technical_score": 88,
        "communication_score": 82,
        "english_score": 85,
        "detailed_metrics": {...},
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
        
        score = float(data.get("score", 0.0))
        # Update best score
        if int(score) > stats.best_interview_score:
            stats.best_interview_score = int(score)
            
        # Update average score
        if stats.interviews_completed == 1:
            stats.avg_interview_score = score
        else:
            stats.avg_interview_score = round((stats.avg_interview_score * (stats.interviews_completed - 1) + score) / stats.interviews_completed, 2)

        # 2. Update Domain Skills in UserSkillScore
        detailed = data.get("detailed_metrics") or {}
        tech_breakdown = detailed.get("technical_breakdown") or {}
        comm_breakdown = detailed.get("communication_breakdown") or {}
        
        skills_to_update = {}
        for k, v in tech_breakdown.items():
            if isinstance(v, (int, float)):
                clean_name = k.replace("_", " ").title()
                skills_to_update[clean_name] = float(v)

        for k, v in comm_breakdown.items():
            if isinstance(v, (int, float)):
                clean_name = k.replace("_", " ").title()
                skills_to_update[f"Comm: {clean_name}"] = float(v)

        if not skills_to_update:
            # Fallback to top-level domain score
            domain_name = (data.get("domain") or data.get("type") or "General").title()
            skills_to_update[domain_name] = score

        for domain, skill_score in skills_to_update.items():
            skill_res = await db.execute(select(UserSkillScore).filter_by(user_id=user_id, domain=domain))
            skill = skill_res.scalars().first()
            if not skill:
                skill = UserSkillScore(user_id=user_id, domain=domain, score=skill_score, problems_solved=1)
                db.add(skill)
            else:
                # Rolling average
                skill.score = round((skill.score + skill_score) / 2.0, 2)
                skill.problems_solved += 1

        # 3. Add Learning Event
        event = LearningEvent(
            user_id=user_id,
            event_type="INTERVIEW_COMPLETED",
            reference_id=data.get("interview_id"),
            score_change=score,
            domain=data.get("type", "General"),
            metadata_json={
                "score": score,
                "type": data.get("type"),
                "technical_score": data.get("technical_score"),
                "communication_score": data.get("communication_score"),
            }
        )
        db.add(event)
        
        await db.commit()
        logger.info(f"Successfully processed InterviewCompleted and updated skills for user {user_id}")

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
