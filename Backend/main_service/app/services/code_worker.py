import asyncio
import json
import logging
import sys
from aio_pika import connect_robust, IncomingMessage
from app.config import settings
from app.database import SessionLocal, redis_client
from app.models.dsa import CodeSubmission, UserProblemStatus
from app.services.docker_runner import run_code_in_docker
from sqlalchemy.future import select
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def process_code_execution(data: dict):
    submission_id = data.get("submission_id")
    if not submission_id:
        logger.error("Code execution event missing submission_id")
        return

    try:
        docker_result = await asyncio.to_thread(
            run_code_in_docker,
            code=data["code"],
            function_name=data["function_name"],
            test_cases_json=data["test_cases_json"],
            language=data["language"],
            test_harness=data.get("test_harness")
        )

        async with SessionLocal() as db:
            result = await db.execute(select(CodeSubmission).filter(CodeSubmission.id == submission_id))
            submission = result.scalars().first()
            if submission:
                status = docker_result.get("status", "Error")
                exec_time = docker_result.get("execution_time_ms")
                mem_used = docker_result.get("memory_used_kb")

                submission.status = status
                submission.error_message = docker_result.get("error_message")
                submission.execution_time_ms = exec_time
                submission.memory_used_kb = mem_used
                submission.passed_tests = docker_result.get("passed_tests")
                submission.total_tests = docker_result.get("total_tests")

                # Update UserProblemStatus for formal submissions
                if submission.is_submission and submission.session_id:
                    status_res = await db.execute(
                        select(UserProblemStatus).filter(
                            UserProblemStatus.user_id == submission.session_id,
                            UserProblemStatus.question_id == submission.question_id
                        )
                    )
                    user_status = status_res.scalars().first()
                    new_status_str = "Solved" if status == "Accepted" else "Attempted"

                    if not user_status:
                        user_status = UserProblemStatus(
                            user_id=submission.session_id,
                            question_id=submission.question_id,
                            status=new_status_str,
                            best_runtime_ms=exec_time if status == "Accepted" else None,
                            best_memory_kb=mem_used if status == "Accepted" else None,
                            last_attempted_at=datetime.now(timezone.utc)
                        )
                        db.add(user_status)
                    else:
                        if new_status_str == "Solved" or user_status.status != "Solved":
                            user_status.status = new_status_str
                        user_status.last_attempted_at = datetime.now(timezone.utc)
                        if status == "Accepted":
                            if user_status.best_runtime_ms is None or (exec_time and exec_time < user_status.best_runtime_ms):
                                user_status.best_runtime_ms = exec_time
                            if user_status.best_memory_kb is None or (mem_used and mem_used < user_status.best_memory_kb):
                                user_status.best_memory_kb = mem_used

                await db.commit()

        await redis_client.publish(f"submission_updates_{submission_id}", json.dumps(docker_result))
        
    except Exception as e:
        logger.error(f"Execution failed for submission {submission_id}: {e}")
        try:
            await redis_client.publish(f"submission_updates_{submission_id}", json.dumps({
                "status": "Error",
                "error_message": str(e)
            }))
            
            async with SessionLocal() as db:
                result = await db.execute(select(CodeSubmission).filter(CodeSubmission.id == submission_id))
                sub = result.scalars().first()
                if sub:
                    sub.status = "Error"
                    sub.error_message = str(e)
                    await db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update error status for submission {submission_id}: {db_err}")


async def handle_code_message(message: IncomingMessage, semaphore: asyncio.Semaphore):
    span_ctx = None
    try:
        from ddtrace import tracer
        if message.headers:
            span_ctx = tracer.extract(message.headers)
    except Exception:
        pass

    try:
        from ddtrace import tracer
        span_cm = tracer.trace("rabbitmq.consume.code_execution", child_of=span_ctx, service="main-service")
    except Exception:
        span_cm = None

    async def _execute():
        async with semaphore:
            try:
                body = message.body.decode()
                data = json.loads(body)
                await process_code_execution(data)
                await message.ack()
            except json.JSONDecodeError as e:
                logger.error(f"Malformed JSON in code execution queue message: {e}")
                await message.reject(requeue=False)
            except Exception as e:
                logger.error(f"Fatal error executing code task: {e}")
                await message.reject(requeue=False)

    if span_cm:
        with span_cm as span:
            await _execute()
    else:
        await _execute()


async def start_code_worker():
    rabbitmq_url = settings.RABBITMQ_URL if hasattr(settings, 'RABBITMQ_URL') else "amqp://guest:guest@localhost:5672/"
    semaphore = asyncio.Semaphore(5)
    
    while True:
        try:
            connection = await connect_robust(rabbitmq_url)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=5)
            queue = await channel.declare_queue("code_execution_queue", durable=True)
            logger.info("Main Service Code Worker started successfully.")
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    asyncio.create_task(handle_code_message(message, semaphore))
                            
        except asyncio.CancelledError:
            logger.info("Code worker task cancelled.")
            break
        except Exception as e:
            logger.error(f"RabbitMQ connection failed in code worker: {e}. Retrying in 5 seconds...")
            try:
                if 'connection' in locals() and connection and not connection.is_closed:
                    await connection.close()
            except Exception:
                pass
            await asyncio.sleep(5)
