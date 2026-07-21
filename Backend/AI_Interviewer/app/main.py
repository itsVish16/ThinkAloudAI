import json
import httpx
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextlib import asynccontextmanager

from app.services.livekit_api import generate_livekit_token
from app.routers import admin
from app.services.events import redis_client
from app.services.auth import get_current_user
from app.services.analysis import analyze_and_save_interview
from app.services.db import get_interview_session, save_interview_session, init_db
import asyncio
from app.config import settings

# Middleware to normalize double slashes in incoming request paths
class NormalizePathMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path", "")
        while "//" in path:
            path = path.replace("//", "/")
        request.scope["path"] = path
        return await call_next(request)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="AI Interviewer API", 
    description="Real-time WebRTC AI Interviewer backend powered by LiveKit and Featherless LLM.",
    version="1.1.0",
    lifespan=lifespan
)

app.include_router(admin.router)

# --- Pydantic Schemas ---

class TokenRequest(BaseModel):
    room_name: str = Field(..., description="Unique identifier for the interview room", examples=["interview_59182"])
    interview_type: str = Field("general", description="Type of interview to conduct", examples=["swe", "pm", "general"])
    question_ids: Optional[List[str]] = Field(None, description="Optional specific question IDs to use for this interview")
    domain: Optional[str] = Field(None, description="Domain context for system design interviews")
    role: Optional[str] = Field(None, description="Target role for system design interviews")

class TokenResponse(BaseModel):
    token: str = Field(..., description="LiveKit JWT access token for WebRTC connection")
    url: str = Field(..., description="LiveKit WebSocket URL to connect to")
    roomName: str = Field(..., description="The requested room name")
    candidate: str = Field(..., description="Extracted candidate username from User Service")
    ai_selected_questions: Optional[List[Dict[str, Any]]] = Field(None, description="Questions selected by the AI for this interview")

class InterviewDetailResponse(BaseModel):
    room_name: str = Field(..., description="The interview room identifier")
    stage: str = Field(..., description="The current stage of the interview state machine")
    candidate_name: str = Field(..., description="Candidate's name")
    transcript: List[Dict[str, Any]] = Field([], description="Full transcript of the conversation")
    evaluation: Optional[Dict[str, Any]] = Field(None, description="Scores and feedback if the interview is completed")
    created_at: str = Field(..., description="ISO timestamp of interview creation")
    updated_at: str = Field(..., description="ISO timestamp of last activity")

class InterviewTypeItem(BaseModel):
    id: str = Field(..., description="The internal ID of the interview type", examples=["swe"])
    name: str = Field(..., description="Human-readable name", examples=["Software Engineering"])
    description: str = Field(..., description="Short description of what the interview covers")

class InterviewTypesResponse(BaseModel):
    types: List[InterviewTypeItem] = Field(..., description="List of available interview types")

app.add_middleware(NormalizePathMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/api/interview-types",
    response_model=InterviewTypesResponse,
    summary="List available interview types",
    description="Returns a list of all currently supported mock interview configurations."
)
async def get_interview_types():
    return {
        "types": [
            {
                "id": "dsa",
                "name": "Data Structures & Algorithms",
                "description": "Technical interview focusing on problem-solving, algorithmic efficiency, and coding."
            },
            {
                "id": "system_design",
                "name": "System Design",
                "description": "Technical interview focusing on architecture, scalability, and system-level trade-offs."
            },
            {
                "id": "hr",
                "name": "HR / Behavioral",
                "description": "Standard behavioral interview using the STAR method."
            },
            {
                "id": "presentation",
                "name": "Presentation Discussion",
                "description": "Evaluate communication skills and deep understanding of a project presentation."
            },
            {
                "id": "ai_ml",
                "name": "AI/ML Engineering",
                "description": "Evaluate deep knowledge of machine learning concepts, models, and MLOps."
            },
            {
                "id": "pm",
                "name": "Product Management",
                "description": "Focuses on product sense, strategy, execution, and behavioral scenarios."
            }
        ]
    }



@app.post(
    "/api/token", 
    response_model=TokenResponse,
    summary="Generate WebRTC Room Token",
    description="Authenticates the user via the central User Service JWT and generates a LiveKit token to connect to the WebRTC room. Injects candidate context into the token metadata.",
    responses={
        200: {"description": "Successfully generated LiveKit token"},
        401: {"description": "Missing or invalid authorization token"}
    }
)
async def get_token(
    payload: TokenRequest,
    current_user: dict = Depends(get_current_user)
):
    username = current_user.get("username", "Candidate")
    user_id = current_user.get("user_id", "guest_user")
    email = current_user.get("email", "unknown@thinkaloudai.tech")

    # Normalize interview_type for AI/ML variants
    if payload.interview_type in ["ml-engineer-infra", "agentic-ai-engineer"]:
        payload.interview_type = "ai_ml"

    import random
    
    # Handle dynamic DSA questions passed via interview_type (e.g. "dsa:1,2")
    if payload.interview_type.startswith("dsa:"):
        parts = payload.interview_type.split(":", 1)
        if len(parts) > 1 and parts[1]:
            # Merge with existing question_ids if any
            extracted_ids = [id_str.strip() for id_str in parts[1].split(",") if id_str.strip()]
            if payload.question_ids:
                payload.question_ids.extend(extracted_ids)
            else:
                payload.question_ids = extracted_ids
        payload.interview_type = "dsa"
        
    ai_selected_questions = []
    try:
        async with httpx.AsyncClient() as client:
            if payload.interview_type == "dsa":
                response = await client.get(f"{settings.MAIN_SERVICE_URL}/dsa/questions")
                if response.status_code == 200:
                    dsa_pool = response.json()
                    if payload.question_ids:
                        ai_selected_questions = [q for q in dsa_pool if str(q["id"]) in payload.question_ids]
                    else:
                        ai_selected_questions = random.sample(dsa_pool, min(2, len(dsa_pool)))
            elif payload.interview_type == "system_design":
                url = f"{settings.MAIN_SERVICE_URL}/system-design/questions"
                query_params = {}
                if payload.domain:
                    query_params["domain"] = payload.domain
                if payload.role:
                    query_params["role"] = payload.role
                
                response = await client.get(url, params=query_params)
                if response.status_code == 200:
                    sd_pool = response.json()
                    if payload.question_ids:
                        ai_selected_questions = [q for q in sd_pool if str(q["id"]) in payload.question_ids or q.get("id") in payload.question_ids]
                    else:
                        ai_selected_questions = random.sample(sd_pool, min(1, len(sd_pool)))
            elif payload.interview_type == "behavioral":
                response = await client.get(f"{settings.MAIN_SERVICE_URL}/behavioral/questions?limit=2")
                if response.status_code == 200:
                    ai_selected_questions = response.json()
            elif payload.interview_type == "product_management" or payload.interview_type == "pm":
                response = await client.get(f"{settings.MAIN_SERVICE_URL}/pm/questions?limit=2")
                if response.status_code == 200:
                    ai_selected_questions = response.json()
            elif payload.interview_type in ["ai_ml", "ml-engineer-infra", "agentic-ai-engineer"]:
                response = await client.get(f"{settings.MAIN_SERVICE_URL}/aiml/questions?limit=2")
                if response.status_code == 200:
                    ai_selected_questions = response.json()
    except Exception as e:
        print(f"Error fetching questions: {e}")

    # Generate room JWT embedding candidate metadata (LiveKit might truncate this, so we ALSO save to DB)
    # We DO NOT embed ai_selected_questions because they can easily exceed LiveKit's 1024-byte metadata limit
    token = generate_livekit_token(
        identity=username, 
        room_name=payload.room_name, 
        user_id=user_id,
        interview_type=payload.interview_type,
        ai_selected_questions=[] # Pass empty to avoid token truncation
    )

    import time
    initial_state = {
        "stage": "intro_audio_check",
        "messages": [],
        "candidate_name": username,
        "resume_summary": "",
        "evaluations": [],
        "start_time": time.time(),
        "max_duration_minutes": 50,
        "interview_type": payload.interview_type,
        "latest_visual_context": None,
        "ai_selected_questions": ai_selected_questions,
        "active_question_index": 0,
        "latest_code": None,
        "latest_execution": None,
        "latest_whiteboard_context": None
    }
    
    # Save session immediately so worker.py can retrieve large question payloads safely
    await save_interview_session(
        session_id=payload.room_name,
        user_id=user_id,
        candidate_name=username,
        interview_type=payload.interview_type,
        stage="intro_audio_check",
        resume_summary=None,
        state_data=initial_state,
        email=email
    )


    return {
        "token": token,
        "url": settings.LIVEKIT_URL,
        "roomName": payload.room_name,
        "candidate": username,
        "ai_selected_questions": ai_selected_questions
    }

@app.get(
    "/api/interview/{room_name}",
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
    
    # Ownership verification
    if session["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to view this interview."
        )
    
    return {
        "room_name": session["id"],
        "stage": session["stage"],
        "candidate_name": session["candidate_name"],
        "transcript": session.get("state_data", {}).get("messages", []) if session.get("state_data") else [],
        "evaluation": session.get("feedback"),
        "created_at": session["created_at"],
        "updated_at": session["updated_at"]
    }

@app.get(
    "/api/interview/{room_name}/stream",
    summary="SSE for Interview Status",
    description="Streams real-time updates for an interview session.",
)
async def stream_interview_status(
    room_name: str,
    current_user: dict = Depends(get_current_user)
):
    from app.services.events import redis_client
    
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

from app.services.db import get_all_interviews_for_user

@app.post(
    "/api/interview/{room_name}/end",
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
    
    # Ownership verification
    if session["user_id"] != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to modify this interview."
        )
        
    if session["stage"] != "completed":
        # Save as completed
        await save_interview_session(
            session_id=session["id"],
            user_id=session["user_id"],
            candidate_name=session["candidate_name"],
            interview_type=session.get("interview_type") or "Behavioral",
            stage="completed",
            resume_summary=None,
            state_data=session["state_data"]
        )
        
        # Trigger background analysis
        state_data = session.get("state_data") or {}
        messages = state_data.get("messages", [])
        opik_trace_id = state_data.get("opik_trace_id", session["id"])
        
        from app.services.rabbitmq import publish_analysis_task
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

@app.get(
    "/api/interviews/me",
    summary="List Past Interviews",
    description="Fetches a summary list of all past interviews for the logged-in user."
)
async def list_my_interviews(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    return await get_all_interviews_for_user(user_id)

from app.services.db import get_user_analytics

@app.get(
    "/api/interviews/me/analytics",
    summary="User Interview Analytics",
    description="Fetches aggregated interview statistics for the logged-in user to populate the dashboard."
)
async def my_interview_analytics(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    return await get_user_analytics(user_id)

@app.get(
    "/api/leaderboard",
    summary="Live Global Leaderboard",
    description="Fetches the top 10 users globally by their cumulative score."
)
async def get_leaderboard(current_user: dict = Depends(get_current_user)):
    from app.services.events import redis_client
    # Fetch top 10 from sorted set
    top_users = await redis_client.zrevrange("global_leaderboard", 0, 9, withscores=True)
    
    leaderboard = []
    for i, (name, score) in enumerate(top_users):
        leaderboard.append({
            "rank": i + 1,
            "candidate_name": name,
            "score": int(score)
        })
        
    username = current_user.get("username", "Candidate")
    
    # Get current user's rank
    user_rank = await redis_client.zrevrank("global_leaderboard", username)
    user_score = await redis_client.zscore("global_leaderboard", username)
    
    my_rank = {
        "rank": user_rank + 1 if user_rank is not None else None,
        "candidate_name": username,
        "score": int(user_score) if user_score is not None else 0
    }
    
    return {
        "leaderboard": leaderboard,
        "me": my_rank
    }
