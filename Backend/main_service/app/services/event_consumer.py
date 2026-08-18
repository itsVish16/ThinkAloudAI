import asyncio
import json
import logging
from aio_pika import connect_robust, IncomingMessage
from app.config import settings
from app.database import SessionLocal
from sqlalchemy.future import select
from app.models.analytics import UserStats, LearningEvent, UserSkillScore

logger = logging.getLogger(__name__)

async def process_interview_completed(data: dict):
    user_id = data.get("user_id")
    if not user_id:
        logger.error("InterviewCompleted event missing user_id")
        return

    async with SessionLocal() as db:
        stats_res = await db.execute(select(UserStats).filter_by(user_id=user_id))
        stats = stats_res.scalars().first()
        
        if not stats:
            stats = UserStats(user_id=user_id)
            db.add(stats)
            
        stats.interviews_completed += 1
        
        score = float(data.get("score", 0.0))
        if int(score) > stats.best_interview_score:
            stats.best_interview_score = int(score)
            
        if stats.interviews_completed == 1:
            stats.avg_interview_score = score
        else:
            stats.avg_interview_score = round((stats.avg_interview_score * (stats.interviews_completed - 1) + score) / stats.interviews_completed, 2)

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
            domain_name = (data.get("domain") or data.get("type") or "General").title()
            skills_to_update[domain_name] = score

        for domain, skill_score in skills_to_update.items():
            skill_res = await db.execute(select(UserSkillScore).filter_by(user_id=user_id, domain=domain))
            skill = skill_res.scalars().first()
            if not skill:
                skill = UserSkillScore(user_id=user_id, domain=domain, score=skill_score, problems_solved=1)
                db.add(skill)
            else:
                skill.score = round((skill.score + skill_score) / 2.0, 2)
                skill.problems_solved += 1

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


async def handle_message(message: IncomingMessage):
    span_ctx = None
    try:
        from ddtrace import tracer
        if message.headers:
            span_ctx = tracer.extract(message.headers)
    except Exception:
        pass

    try:
        from ddtrace import tracer
        span_cm = tracer.trace("rabbitmq.consume.interview_completed", child_of=span_ctx, service="main-service")
    except Exception:
        span_cm = None

    async def _execute():
        async with message.process():
            try:
                body = message.body.decode()
                event = json.loads(body)
                if event.get("event") == "InterviewCompleted":
                    await process_interview_completed(event.get("data", {}))
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    if span_cm:
        with span_cm as span:
            await _execute()
    else:
        await _execute()


async def start_event_consumer():
    rabbitmq_url = settings.RABBITMQ_URL if hasattr(settings, 'RABBITMQ_URL') else "amqp://guest:guest@localhost:5672/"
    while True:
        try:
            connection = await connect_robust(rabbitmq_url)
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "thinkaloud_events",
                type="topic",
                durable=True
            )
            queue = await channel.declare_queue("main_service_events", durable=True)
            await queue.bind(exchange, routing_key="interview.completed")
            logger.info("Event consumer connected and listening for thinkaloud_events.")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await handle_message(message)
        except asyncio.CancelledError:
            logger.info("Event consumer task cancelled.")
            break
        except Exception as e:
            logger.error(f"RabbitMQ connection failed in event consumer: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
