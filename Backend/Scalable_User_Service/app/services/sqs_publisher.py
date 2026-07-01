import json
import structlog
import aioboto3

from app.config import settings

logger = structlog.get_logger(__name__)

# Create a global session to avoid recreating it on every request (which takes ~10 seconds)
aws_session = aioboto3.Session(
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
    region_name=settings.aws_region or "us-east-1"
)

async def publish_email_task(task_type: str, email: str, payload: dict) -> None:
    """
    Publish an email task to the SQS queue.
    """
    if not settings.sqs_email_queue_url:
        logger.warning("sqs_email_queue_url_not_set", task_type=task_type, email=email)
        return

    message_body = json.dumps({
        "type": task_type,
        "email": email,
        "payload": payload
    })

    try:
        async with aws_session.client("sqs") as client:
            response = await client.send_message(
                QueueUrl=settings.sqs_email_queue_url,
                MessageBody=message_body
            )
            logger.info("sqs_message_published", message_id=response.get("MessageId"), task_type=task_type, email=email)
    except Exception as e:
        logger.error("sqs_message_publish_failed", error=str(e), task_type=task_type, email=email)
