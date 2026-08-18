import asyncio
import json
import logging
import sys
import aio_pika

from app.config import settings
from app.services.analysis import analyze_and_save_interview
from app.services.rabbitmq import get_rabbitmq_channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analysis_worker")


async def process_message(message: aio_pika.IncomingMessage):
    """
    Process an incoming analysis task from RabbitMQ with Datadog APM span continuation.
    """
    span_ctx = None
    try:
        from ddtrace import tracer
        if message.headers:
            span_ctx = tracer.extract(message.headers)
    except Exception:
        pass

    try:
        from ddtrace import tracer
        span_cm = tracer.trace("rabbitmq.consume.interview_analysis", child_of=span_ctx, service="ai-interviewer-analysis-worker")
    except Exception:
        span_cm = None

    async def _execute_analysis(span=None):
        async with message.process(requeue=True):
            try:
                payload = json.loads(message.body.decode())
                if span:
                    span.set_tag("interview.session_id", payload.get("session_id"))
                    span.set_tag("usr.id", payload.get("user_id"))
                    span.set_tag("interview.type", payload.get("interview_type"))
                logger.info(f"Received analysis task for session: {payload.get('session_id')}")

                await analyze_and_save_interview(
                    session_id=payload["session_id"],
                    user_id=payload["user_id"],
                    candidate_name=payload["candidate_name"],
                    interview_type=payload.get("interview_type", "Behavioral"),
                    messages=payload.get("messages", []),
                    opik_trace_id=payload.get("opik_trace_id"),
                )
                logger.info(f"Successfully processed analysis task for session: {payload.get('session_id')}")
            except Exception as e:
                logger.error(f"Failed to process analysis task: {e}")
                if span:
                    span.set_exc_info(*sys.exc_info())
                raise

    if span_cm:
        with span_cm as span:
            await _execute_analysis(span)
    else:
        await _execute_analysis(None)


async def start_worker():
    logger.info("Starting Interview Analysis RabbitMQ Worker...")
    channel = await get_rabbitmq_channel()
    await channel.set_qos(prefetch_count=1)
    queue = await channel.get_queue("interview_analysis_queue")
    logger.info("Waiting for messages on 'interview_analysis_queue'.")
    await queue.consume(process_message)
    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(start_worker())
    except KeyboardInterrupt:
        logger.info("Analysis worker stopped.")
