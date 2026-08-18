import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.events import publish_interview_completed


@pytest.mark.asyncio
async def test_publish_interview_completed_format():
    mock_exchange = AsyncMock()
    mock_channel = AsyncMock()
    mock_channel.declare_exchange = AsyncMock(return_value=mock_exchange)

    mock_connection = AsyncMock()
    mock_connection.channel = AsyncMock(return_value=mock_channel)
    mock_connection.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_connection.__aexit__ = AsyncMock(return_value=None)

    session_id = "test_session_abc_123"
    user_id = "usr_456"
    candidate_name = "Alice Candidate"
    domain = "dsa"
    overall_score = 88
    interview_type = "dsa"
    feedback_text = "Solid understanding of trees and dynamic programming."
    detailed_metrics = {
        "technical_breakdown": {"algorithms": 90, "optimization": 85},
        "communication_breakdown": {"clarity": 90},
    }

    with patch("app.services.events.aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect, \
         patch("app.services.events.redis_client") as mock_redis:

        mock_connect.return_value = mock_connection
        mock_redis.publish = AsyncMock()
        mock_redis.zscore = AsyncMock(return_value=None)
        mock_redis.zadd = AsyncMock()

        result = await publish_interview_completed(
            session_id=session_id,
            user_id=user_id,
            candidate_name=candidate_name,
            domain=domain,
            overall_score=overall_score,
            interview_type=interview_type,
            feedback_text=feedback_text,
            detailed_metrics=detailed_metrics,
        )

        # 1. Verify returned payload format
        assert result["event"] == "InterviewCompleted"
        data = result["data"]
        assert data["interview_id"] == session_id
        assert data["user_id"] == user_id
        assert data["score"] == overall_score
        assert data["type"] == interview_type
        assert data["domain"] == domain
        assert data["feedback"] == feedback_text
        assert data["detailed_metrics"] == detailed_metrics

        # 2. Verify RabbitMQ exchange declaration & publish
        mock_channel.declare_exchange.assert_called_once()
        args, kwargs = mock_channel.declare_exchange.call_args
        assert args[0] == "thinkaloud_events"

        mock_exchange.publish.assert_called_once()
        pub_args, pub_kwargs = mock_exchange.publish.call_args
        assert pub_kwargs["routing_key"] == "interview.completed"
        published_msg = pub_args[0]
        published_payload = json.loads(published_msg.body.decode())
        assert published_payload["event"] == "InterviewCompleted"
        assert published_payload["data"]["interview_id"] == session_id

        # 3. Verify Redis publish & leaderboard update
        mock_redis.publish.assert_called_once_with("interview_events", json.dumps(result))
        mock_redis.zadd.assert_called_once_with("global_leaderboard", {candidate_name: overall_score})
