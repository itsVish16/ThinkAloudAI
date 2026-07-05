import json
import logging
import asyncio
import os
import re
from app.agent.prompts import POST_INTERVIEW_ANALYSIS_PROMPT
from app.agent.llm import call_llm, _track
from app.services.db import AsyncSessionLocal
from app.models.interview import InterviewFeedback
from app.services.events import publish_interview_completed

logger = logging.getLogger("analysis_service")

def format_transcript(messages: list) -> str:
    transcript = ""
    for msg in messages:
        if msg["role"] == "system": continue
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        transcript += f"{role}: {msg['content']}\n\n"
    return transcript

import httpx
from app.config import settings

async def get_code_submissions(session_id: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.MAIN_SERVICE_URL}/dsa/submissions/{session_id}", timeout=10.0)
            if response.status_code == 200:
                submissions = response.json()
                if not submissions:
                    return "No code submissions found."
                
                formatted = ""
                for i, sub in enumerate(submissions):
                    formatted += f"--- Submission {i+1} ---\n"
                    formatted += f"Language: {sub.get('language')}\n"
                    formatted += f"Status: {sub.get('status')}\n"
                    if sub.get('error_message'):
                        formatted += f"Error: {sub.get('error_message')}\n"
                    formatted += f"Code:\n{sub.get('code')}\n\n"
                return formatted
            return "Could not retrieve code submissions."
    except Exception as e:
        logger.error(f"Failed to fetch code submissions: {e}")
        return "Failed to fetch code submissions."

@_track(name="post_interview_analysis", type="llm")
async def analyze_and_save_interview(session_id: str, user_id: str, candidate_name: str, interview_type: str, messages: list):
    """
    Background task to analyze transcript, generate feedback, save to DB, and publish event.
    """
    logger.info(f"Starting post-interview analysis for session {session_id}")
    
    transcript = format_transcript(messages)
    code_subs_text = await get_code_submissions(session_id)
    
    prompt = POST_INTERVIEW_ANALYSIS_PROMPT.format(
        interview_type=interview_type,
        transcript=transcript,
        code_submissions=code_subs_text
    )
    
    eval_messages = []
    
    try:
        raw_response = await call_llm(eval_messages, prompt)
        
        # Resilient JSON extraction
        json_match = re.search(r'\{.*\}', raw_response.replace('\n', ' '), re.DOTALL)
        if json_match:
            raw_response = json_match.group(0)
            
        data = json.loads(raw_response)
        
        # Save to DB
        async with AsyncSessionLocal() as db:
            feedback = InterviewFeedback(
                session_id=session_id,
                technical_score=data.get("technical_score", 0),
                communication_score=data.get("communication_score", 0),
                english_score=data.get("english_score", 0),
                strengths=json.dumps(data.get("strengths", [])),
                weaknesses=json.dumps(data.get("weaknesses", [])),
                improvement_plan=json.dumps(data.get("improvement_plan", [])),
                recommended_topics=data.get("recommended_topics", [])
            )
            db.add(feedback)
            await db.commit()
            
        logger.info(f"Successfully saved feedback for session {session_id}")
        
        # Average score
        overall_score = (data.get("technical_score", 0) + data.get("communication_score", 0) + data.get("english_score", 0)) // 3
        
        await publish_interview_completed(
            session_id=session_id,
            user_id=user_id,
            domain=interview_type,
            overall_score=overall_score,
            interview_type=interview_type,
            technical_score=data.get("technical_score"),
            communication_score=data.get("communication_score"),
            english_score=data.get("english_score"),
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode LLM JSON response for session {session_id}: {e}\nRaw Output: {raw_response}")
    except Exception as e:
        logger.error(f"Failed to analyze and save interview for session {session_id}: {e}")
