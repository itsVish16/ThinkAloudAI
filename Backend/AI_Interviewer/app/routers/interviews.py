import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.auth import get_current_user
from app.services.events import redis_client
from app.services.db import get_interview_session, save_interview_session, get_all_interviews_for_user
from app.services.rabbitmq import publish_analysis_task

router = APIRouter(prefix="/api", tags=["interviews"])


class InterviewDetailResponse(BaseModel):
    room_name: str = Field(..., description="The interview room identifier")
    stage: str = Field(..., description="The current stage of the interview state machine")
    candidate_name: str = Field(..., description="Candidate's name")
    transcript: List[Dict[str, Any]] = Field(default_factory=list, description="Full transcript of the conversation")
    evaluation: Optional[Dict[str, Any]] = Field(None, description="Scores and feedback if the interview is completed")
    created_at: Optional[str] = Field(None, description="ISO timestamp of interview creation")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last activity")


@router.get(
    "/interview/{room_name}",
    response_model=InterviewDetailResponse,
    summary="Retrieve Interview Transcript",
    description="Fetches the full JSON transcript, active stage, and generated evaluation for a specific interview room. Verifies ownership so users can only view their own interviews.",
    responses={
        200: {"description": "Interview details retrieved successfully"},
        401: {"description": "Missing or invalid authorization token"},
        403: {"description": "User does not own this interview session"},
        404: {"description": "Interview session not found"}
    }
)
async def get_interview_details(
    room_name: str,
    current_user: dict = Depends(get_current_user)
):
    session = await get_interview_session(room_name)
    if not session:
        raise HTTPException(status_code=404, detail="Interview Session not found...")
    
    if session["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to view this interview."
        )
    
    raw_messages = session.get("state_data", {}).get("messages", []) if session.get("state_data") else []
    cleaned_transcript = []
    import re
    for msg in raw_messages:
        if msg.get("role") == "system":
            continue
        content = msg.get("content", "")
        # Remove internal observation/system tags
        content = re.sub(r"\[Candidate Visual Observation:.*?\]\s*", "", content)
        content = re.sub(r"\[Candidate Whiteboard Observation:.*?\]\s*", "", content)
        content = re.sub(r"\[Candidate says:\s*", "", content)
        content = re.sub(r"\[SYSTEM:.*?\]\s*", "", content)
        content = content.strip()
        if content:
            cleaned_transcript.append({
                "role": msg.get("role"),
                "content": content
            })

    return {
        "room_name": session["id"],
        "stage": session["stage"],
        "candidate_name": session["candidate_name"],
        "transcript": cleaned_transcript,
        "evaluation": session.get("feedback"),
        "created_at": session["created_at"],
        "updated_at": session["updated_at"]
    }


@router.get(
    "/interview/{room_name}/stream",
    summary="SSE for Interview Status",
    description="Streams real-time updates for an interview session.",
)
async def stream_interview_status(
    room_name: str,
    current_user: dict = Depends(get_current_user)
):
    session = await get_interview_session(room_name)
    if not session:
        raise HTTPException(status_code=404, detail="Interview Session not found")
    if session["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this interview")
    
    async def event_generator():
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("interview_events")
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    try:
                        data = json.loads(message["data"])
                        if data.get("event") == "InterviewCompleted" and data.get("data", {}).get("interview_id") == room_name:
                            yield f"data: {json.dumps(data)}\n\n"
                            break
                    except json.JSONDecodeError:
                        pass
                yield ": keep-alive\n\n"
                await asyncio.sleep(1)
        finally:
            await pubsub.unsubscribe("interview_events")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post(
    "/interview/{room_name}/end",
    summary="Force End Interview",
    description="Manually ends an active interview session and triggers the background analysis pipeline.",
    responses={
        200: {"description": "Interview ended successfully"},
        401: {"description": "Missing or invalid authorization token"},
        403: {"description": "User does not own this interview session"},
        404: {"description": "Interview session not found"}
    }
)
async def force_end_interview(
    room_name: str,
    current_user: dict = Depends(get_current_user)
):
    session = await get_interview_session(room_name)
    if not session:
        raise HTTPException(status_code=404, detail="Interview Session not found...")
    
    if session["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to modify this interview."
        )
        
    if session["stage"] != "completed":
        state_data = session.get("state_data") or {}
        await save_interview_session(
            session_id=session["id"],
            user_id=session["user_id"],
            candidate_name=session["candidate_name"],
            interview_type=session.get("interview_type") or "Behavioral",
            stage="completed",
            resume_summary=None,
            state_data=state_data
        )
        
        messages = state_data.get("messages", [])
        opik_trace_id = state_data.get("opik_trace_id", session["id"])
        
        payload = {
            "session_id": session["id"],
            "user_id": session["user_id"],
            "candidate_name": session["candidate_name"],
            "interview_type": session.get("interview_type") or "Behavioral",
            "messages": messages,
            "opik_trace_id": opik_trace_id
        }
        asyncio.create_task(publish_analysis_task(payload))
    
    return {"status": "success", "message": "Interview marked as completed and analysis triggered"}


@router.get(
    "/interviews/me",
    summary="List Past Interviews",
    description="Fetches a summary list of all past interviews for the logged-in user."
)
async def list_my_interviews(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    return await get_all_interviews_for_user(user_id)
