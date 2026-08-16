import asyncio
import json
import logging
from aio_pika import connect_robust, IncomingMessage
from app.config import settings
from app.database import SessionLocal, redis_client
from app.models.dsa import CodeSubmission
from app.services.docker_runner import run_code_in_docker
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

async def process_code_execution(data: dict):
    """
    Executes the code using docker_runner and updates DB and Redis Pub/Sub.
    """
    submission_id = data.get("submission_id")
    if not submission_id:
        logger.error("Code execution event missing submission_id")
        return

    try:
        # Run code synchronously in a thread pool so we don't block the asyncio event loop
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
                submission.status = docker_result.get("status", "Error")
                submission.error_message = docker_result.get("error_message")
                submission.execution_time_ms = docker_result.get("execution_time_ms")
                submission.memory_used_kb = docker_result.get("memory_used_kb")
                submission.passed_tests = docker_result.get("passed_tests")
                submission.total_tests = docker_result.get("total_tests")
                await db.commit()

        # Publish the result to Redis for SSE listeners
        await redis_client.publish(f"submission_updates_{submission_id}", json.dumps(docker_result))
        
    except Exception as e:
        logger.error(f"Execution failed for submission {submission_id}: {e}")
        # Try to publish error state
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
    """
    Processes a single code execution message with explicit acknowledgment and retry handling.
    ACK happens strictly after task completion.
    """
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
            logger.error(f"Error executing code task: {e}")
            await message.reject(requeue=True)


async def start_code_worker():
    """
    Listens to code_execution_queue and processes code runs with concurrency control
    and reliable acknowledgment after task completion.
    """
    rabbitmq_url = settings.RABBITMQ_URL if hasattr(settings, 'RABBITMQ_URL') else "amqp://guest:guest@localhost:5672/"
    semaphore = asyncio.Semaphore(5)
    
    while True:
        try:
            connection = await connect_robust(rabbitmq_url)
            channel = await connection.channel()
            # Prefetch count determines how many concurrent unacked jobs this worker takes
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
