import asyncio
import json
import logging
import os
import aio_pika
from dotenv import load_dotenv

from app.services.analysis import analyze_and_save_interview
from app.services.rabbitmq import get_rabbitmq_channel

load_dotenv(".env.local", override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analysis_worker")

async def process_message(message: aio_pika.IncomingMessage):
    """
    Process an incoming analysis task from RabbitMQ.
    """
    async with message.process(requeue=False):
        try:
            payload = json.loads(message.body.decode())
            logger.info(f"Received analysis task for session: {payload.get('session_id')}")
            
            await analyze_and_save_interview(
                session_id=payload["session_id"],
                user_id=payload["user_id"],
                candidate_name=payload["candidate_name"],
                interview_type=payload.get("interview_type", "Behavioral"),
                messages=payload.get("messages", []),
                opik_trace_id=payload.get("opik_trace_id")
            )
            logger.info(f"Successfully processed analysis task for session: {payload.get('session_id')}")
        except Exception as e:
            logger.error(f"Failed to process analysis task: {e}")
            # If we raise an exception, `message.process(requeue=True)` will nack the message 
            # and it will be safely returned to the queue for retry.
            raise

async def start_worker():
    """
    Connect to RabbitMQ and start consuming messages.
    """
    logger.info("Starting Interview Analysis RabbitMQ Worker...")
    channel = await get_rabbitmq_channel()
    
    # We want to process only 1 analysis task at a time per worker instance 
    # to avoid OOM or overwhelming the LLM API.
    await channel.set_qos(prefetch_count=1)
    
    queue = await channel.get_queue("interview_analysis_queue")
    
    logger.info("Waiting for messages on 'interview_analysis_queue'.")
    await queue.consume(process_message)
    
    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(start_worker())
    except KeyboardInterrupt:
        logger.info("Analysis worker stopped.")
