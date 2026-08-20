import json
import logging
import asyncio
import os
import re
from app.agent.prompts import POST_INTERVIEW_ANALYSIS_PROMPT
from app.agent.llm import call_analysis_llm, _track
from app.services.db import AsyncSessionLocal
from app.models.interview import InterviewFeedback
from app.services.events import publish_interview_completed

logger = logging.getLogger("analysis_service")

def format_transcript(messages: list) -> str:
    transcript = ""
    for msg in messages:
        if msg.get("role") == "system": continue
        role = "Interviewer" if msg.get("role") == "assistant" else "Candidate"
        content = msg.get("content", "")
        # Clean out internal observation or system prompt tags
        content = re.sub(r"\[Candidate Visual Observation:.*?\]\s*", "", content)
        content = re.sub(r"\[Candidate Whiteboard Observation:.*?\]\s*", "", content)
        content = re.sub(r"\[SYSTEM:.*?\]\s*", "", content)
        if content.strip():
            transcript += f"{role}: {content.strip()}\n\n"
    return transcript

def extract_speaking_analytics(messages: list) -> dict:
    candidate_words = 0
    ai_words = 0
    filler_counts = {"umm": 0, "like": 0, "basically": 0}
    
    for msg in messages:
        if msg.get("role") == "system": continue
        content = msg.get("content", "")
        content = re.sub(r"\[Candidate Visual Observation:.*?\]\s*", "", content)
        content = re.sub(r"\[Candidate Whiteboard Observation:.*?\]\s*", "", content)
        content = re.sub(r"\[SYSTEM:.*?\]\s*", "", content)
        
        words = content.split()
        if msg.get("role") == "assistant":
            ai_words += len(words)
        else:
            candidate_words += len(words)
            text_lower = content.lower()
            filler_counts["umm"] += len(re.findall(r'\bumm+\b', text_lower))
            filler_counts["like"] += len(re.findall(r'\blike\b', text_lower))
            filler_counts["basically"] += len(re.findall(r'\bbasically\b', text_lower))
            
    total_words = candidate_words + ai_words
    candidate_pct = int((candidate_words / total_words * 100)) if total_words > 0 else 0
    ai_pct = int((ai_words / total_words * 100)) if total_words > 0 else 0
    
    return {
        "candidate_percentage": candidate_pct,
        "ai_percentage": ai_pct,
        "filler_words": filler_counts
    }

import httpx
from app.config import settings
from app.services.http_client import http_client

from sqlalchemy import select
from app.models.interview import InterviewSession, InterviewFeedback

async def get_code_submissions(session_id: str) -> str:
    # 1. First attempt to fetch formal submissions from Main Service
    try:
        response = await http_client.get(f"{settings.MAIN_SERVICE_URL}/dsa/submissions/{session_id}", timeout=10.0)
        if response.status_code == 200:
            submissions = response.json()
            if submissions:
                formatted = ""
                for i, sub in enumerate(submissions):
                    formatted += f"--- Submission {i+1} ---\n"
                    formatted += f"Language: {sub.get('language')}\n"
                    formatted += f"Status: {sub.get('status')}\n"
                    if sub.get('error_message'):
                        formatted += f"Error: {sub.get('error_message')}\n"
                    formatted += f"Code:\n{sub.get('code')}\n\n"
                return formatted
    except Exception as e:
        logger.warning(f"Failed to fetch formal submissions from main_service: {e}")

    # 2. Fallback to latest unsubmitted code from session state
    try:
        async with AsyncSessionLocal() as db:
            session_res = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
            sess = session_res.scalar_one_or_none()
            if sess and sess.state_data:
                latest_code = sess.state_data.get("latest_code")
                latest_exec = sess.state_data.get("latest_execution")
                if latest_code:
                    formatted = "--- Latest Unsubmitted Code Snapshot ---\n"
                    if latest_exec:
                        formatted += f"Execution Result: {latest_exec}\n"
                    formatted += f"Code:\n{latest_code}\n\n"
                    return formatted
    except Exception as db_err:
        logger.error(f"Failed to fetch code snapshot fallback from db: {db_err}")

    return "No code submissions or editor code found."

async def analyze_and_save_interview(session_id: str, user_id: str, candidate_name: str, interview_type: str, messages: list, opik_trace_id: str = None):
    """
    Background task to analyze transcript, generate feedback, save to DB, and publish event.
    """
    logger.info(f"Starting post-interview analysis for session {session_id}")
    
    # Explicit Opik span tracking to keep it in the same thread
    span = None
    try:
        import opik
        if opik_trace_id:
            trace = opik.Trace(id=opik_trace_id)
            span = trace.span(name="post_interview_analysis", type="llm")
    except Exception:
        pass
        
    transcript = format_transcript(messages)
    code_subs_text = await get_code_submissions(session_id)
    
    i_type = interview_type.lower()
    if "system_design" in i_type or "sd" in i_type:
        schema_str = """{{
        "requirements_gathering": <int 0-100>,
        "high_level_architecture": <int 0-100>,
        "scalability_and_capacity": <int 0-100>,
        "trade_off_reasoning": <int 0-100>,
        "communication": <int 0-100>
    }}"""
    elif "behavioral" in i_type or "hr" in i_type:
        schema_str = """{{
        "star_structure": <int 0-100>,
        "specificity": <int 0-100>,
        "ownership_and_impact": <int 0-100>,
        "clarity": <int 0-100>,
        "conciseness": <int 0-100>
    }}"""
    elif "pm" in i_type or "product" in i_type:
        schema_str = """{{
        "user_empathy_and_scoping": <int 0-100>,
        "product_sense_and_vision": <int 0-100>,
        "prioritization_framework": <int 0-100>,
        "metrics_and_tradeoffs": <int 0-100>,
        "communication": <int 0-100>
    }}"""
    elif any(k in i_type for k in ["ai_ml", "ml-engineer", "agentic-ai", "machine_learning"]):
        schema_str = """{{
        "ml_fundamentals": <int 0-100>,
        "model_selection": <int 0-100>,
        "data_processing": <int 0-100>,
        "system_architecture": <int 0-100>,
        "communication": <int 0-100>
    }}"""
    else:
        schema_str = """{{
        "algorithms": <int 0-100>,
        "time_complexity": <int 0-100>,
        "edge_cases": <int 0-100>,
        "optimization": <int 0-100>,
        "code_quality": <int 0-100>
    }}"""

    prompt = POST_INTERVIEW_ANALYSIS_PROMPT.format(
        interview_type=interview_type,
        transcript=transcript,
        code_submissions=code_subs_text,
        technical_breakdown_schema=schema_str
    )
    
    # Send the massive prompt as a user message instead of a system prompt to avoid truncation
    eval_messages = [{"role": "user", "content": prompt}]
    system_prompt = "You are an expert AI Interview Evaluator."
    
    # Check transcript quality
    speaking_analytics = extract_speaking_analytics(messages)
    
    if len(messages) < 3:
        logger.warning(f"Transcript for {session_id} has less than 3 messages. Skipping deep analysis.")
        try:
            async with AsyncSessionLocal() as db:
                feedback = InterviewFeedback(
                    session_id=session_id,
                    technical_score=0,
                    communication_score=0,
                    english_score=0,
                    strengths=json.dumps(["Not enough conversation data"]),
                    weaknesses=json.dumps(["Session disconnected immediately"]),
                    improvement_plan=json.dumps(["Complete a full interview session to receive scores"]),
                    recommended_topics=[],
                    detailed_metrics={
                        "hiring_decision": "Reject",
                        "executive_summary": "The interview session was ended immediately without sufficient conversation.",
                        "speaking_analytics": speaking_analytics
                    }
                )
                db.add(feedback)
                await db.commit()
            
            await publish_interview_completed(
                session_id=session_id, user_id=user_id, candidate_name=candidate_name, domain=interview_type,
                overall_score=0, interview_type=interview_type,
                technical_score=0, communication_score=0, english_score=0,
            )
        except Exception as e:
            logger.error(f"Error saving short transcript fallback for {session_id}: {e}")
        finally:
            if span:
                try: span.end(output={"status": "skipped_too_short"})
                except Exception: pass
        return

    MAX_RETRIES = 3
    data = None
    
    for attempt in range(MAX_RETRIES):
        try:
            raw_response = await call_analysis_llm(eval_messages, system_prompt, opik_trace_id=opik_trace_id)
            
            # Resilient JSON extraction
            cleaned = raw_response.strip()
            if "```" in cleaned:
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned = cleaned[start_idx : end_idx + 1]
            data = json.loads(cleaned)
            break # Success, exit retry loop
            
        except json.JSONDecodeError as e:
            logger.error(f"Attempt {attempt+1} - Failed to decode LLM JSON response for session {session_id}: {e}")
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Max retries reached. Raw Output: {raw_response}")
                raise e
            await asyncio.sleep(2 ** attempt) # Exponential backoff
        except Exception as e:
            logger.error(f"Attempt {attempt+1} - LLM call failed: {e}")
            if attempt == MAX_RETRIES - 1:
                raise e
            await asyncio.sleep(2 ** attempt)
            
    if not data:
        logger.error(f"Analysis failed to produce valid data after {MAX_RETRIES} attempts for session {session_id}")
        if span:
            try: span.end(output={"status": "failed_no_data"})
            except Exception: pass
        return

    try:
        detailed_metrics = {
            "hiring_decision": data.get("hiring_decision", "Borderline"),
            "executive_summary": data.get("executive_summary", ""),
            "technical_breakdown": data.get("technical_breakdown", {}),
            "communication_breakdown": data.get("communication_breakdown", {}),
            "speaking_analytics": speaking_analytics
        }
        
        # Save to DB (idempotent — update if feedback already exists)
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            existing = (await db.execute(
                select(InterviewFeedback).where(InterviewFeedback.session_id == session_id)
            )).scalar_one_or_none()

            if existing:
                logger.info(f"Feedback already exists for {session_id}, updating.")
                existing.technical_score = data.get("technical_score", 0)
                existing.communication_score = data.get("communication_score", 0)
                existing.english_score = data.get("english_score", 0)
                existing.strengths = json.dumps(data.get("strengths", []))
                existing.weaknesses = json.dumps(data.get("weaknesses", []))
                existing.improvement_plan = json.dumps(data.get("improvement_plan", []))
                existing.recommended_topics = data.get("recommended_topics", [])
                existing.detailed_metrics = detailed_metrics
            else:
                feedback = InterviewFeedback(
                    session_id=session_id,
                    technical_score=data.get("technical_score", 0),
                    communication_score=data.get("communication_score", 0),
                    english_score=data.get("english_score", 0),
                    strengths=json.dumps(data.get("strengths", [])),
                    weaknesses=json.dumps(data.get("weaknesses", [])),
                    improvement_plan=json.dumps(data.get("improvement_plan", [])),
                    recommended_topics=data.get("recommended_topics", []),
                    detailed_metrics=detailed_metrics
                )
                db.add(feedback)
            await db.commit()
            
        logger.info(f"Successfully saved feedback for session {session_id}")
        
        # Domain-weighted overall score
        tech = data.get("technical_score", 0)
        comm = data.get("communication_score", 0)
        eng = data.get("english_score", 0)

        i_type_clean = interview_type.lower()
        if any(k in i_type_clean for k in ["dsa", "swe", "coding"]):
            overall_score = round(0.60 * tech + 0.25 * comm + 0.15 * eng)
        elif any(k in i_type_clean for k in ["system_design", "sd"]):
            overall_score = round(0.55 * tech + 0.30 * comm + 0.15 * eng)
        elif any(k in i_type_clean for k in ["behavioral", "hr"]):
            overall_score = round(0.20 * tech + 0.70 * comm + 0.10 * eng)
        elif any(k in i_type_clean for k in ["pm", "product"]):
            overall_score = round(0.55 * tech + 0.35 * comm + 0.10 * eng)
        elif any(k in i_type_clean for k in ["ai", "ml"]):
            overall_score = round(0.60 * tech + 0.25 * comm + 0.15 * eng)
        else:
            overall_score = round(0.40 * tech + 0.40 * comm + 0.20 * eng)
        
        await publish_interview_completed(
            session_id=session_id,
            user_id=user_id,
            candidate_name=candidate_name,
            domain=interview_type,
            overall_score=overall_score,
            interview_type=interview_type,
            technical_score=data.get("technical_score"),
            communication_score=data.get("communication_score"),
            english_score=data.get("english_score"),
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze and save interview for session {session_id}: {e}")

    if span:
        try:
            span.end(output={"status": "completed"})
        except Exception:
            pass

