import asyncio
import json
from app.services.db import AsyncSessionLocal, InterviewSession
from app.services.analysis import analyze_and_save_interview
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    async with AsyncSessionLocal() as db:
        # Find interviews that are completed but don't have feedback
        result = await db.execute(select(InterviewSession).options(selectinload(InterviewSession.feedback)).where(InterviewSession.stage == "completed").order_by(InterviewSession.created_at.desc()))
        sessions = result.scalars().all()
        
        for session in sessions:
            if not session.feedback:
                print(f"Re-analyzing session {session.id} ({session.candidate_name})...")
                state_data = session.state_data or {}
                messages = state_data.get("messages", [])
                try:
                    await analyze_and_save_interview(
                        session_id=session.id,
                        user_id=session.user_id,
                        candidate_name=session.candidate_name,
                        interview_type=session.interview_type or "Behavioral",
                        messages=messages
                    )
                    print(f"Successfully analyzed {session.id}")
                except Exception as e:
                    print(f"Failed to analyze {session.id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
