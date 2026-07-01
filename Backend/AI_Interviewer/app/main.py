import json
import httpx
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextlib import asynccontextmanager

from app.services.livekit_api import generate_livekit_token
from app.services.db import get_interview_session, init_db
from app.services.auth import get_current_user
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

# --- Pydantic Schemas ---

class TokenRequest(BaseModel):
    room_name: str = Field(..., description="Unique identifier for the interview room", examples=["interview_59182"])
    interview_type: str = Field("general", description="Type of interview to conduct", examples=["swe", "pm", "general"])
    question_ids: Optional[List[str]] = Field(None, description="Optional specific question IDs to use for this interview")

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

    import random
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
                response = await client.get(f"{settings.MAIN_SERVICE_URL}/system-design/questions")
                if response.status_code == 200:
                    sd_pool = response.json()
                    if payload.question_ids:
                        ai_selected_questions = [q for q in sd_pool if str(q["id"]) in payload.question_ids or q.get("id") in payload.question_ids]
                    else:
                        ai_selected_questions = random.sample(sd_pool, min(1, len(sd_pool)))
    except Exception as e:
        print(f"Error fetching questions: {e}")

    # Generate room JWT embedding candidate metadata
    token = generate_livekit_token(
        identity=username, 
        room_name=payload.room_name, 
        user_id=user_id,
        interview_type=payload.interview_type,
        ai_selected_questions=ai_selected_questions
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
        "transcript": session["state_data"].get("messages", []),
        "evaluation": session.get("feedback"),
        "updated_at": session["updated_at"]
    }

from app.services.db import get_all_interviews_for_user

@app.get(
    "/api/interviews/me",
    summary="List Past Interviews",
    description="Fetches a summary list of all past interviews for the logged-in user."
)
async def list_my_interviews(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    return await get_all_interviews_for_user(user_id)
