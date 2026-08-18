import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.event_consumer import process_interview_completed
from app.models.analytics import UserStats

@pytest.mark.asyncio
async def test_process_interview_completed(monkeypatch):
    data = {
        "user_id": "user_123",
        "interview_id": "int_456",
        "score": 85.5,
        "type": "System Design"
    }

    mock_db = AsyncMock()
    
    # Existing stats mock
    existing_stats = UserStats(
        user_id="user_123",
        interviews_completed=1,
        avg_interview_score=80.0,
        best_interview_score=80
    )
    
    # Mock execute results based on query
    def mock_execute_side_effect(statement):
        mock_res = MagicMock()
        statement_str = str(statement)
        if "user_stats" in statement_str:
            mock_res.scalars().first.return_value = existing_stats
        elif "user_skill_scores" in statement_str:
            mock_res.scalars().first.return_value = None
        else:
            mock_res.scalars().first.return_value = None
        return mock_res

    mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

    # Mock SessionLocal context manager
    class MockSessionManager:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("app.services.event_consumer.SessionLocal", MockSessionManager)

    await process_interview_completed(data)

    # Verify logic updates
    assert existing_stats.interviews_completed == 2
    assert existing_stats.best_interview_score == 85  # Updated to 85 since 85.5 > 80
    assert existing_stats.avg_interview_score == 82.75
    
    # Verify add was called (for skill score and learning event)
    assert mock_db.add.call_count >= 1
    mock_db.commit.assert_called_once()
