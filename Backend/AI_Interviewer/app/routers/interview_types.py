import random
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import time

from app.config import settings
from app.services.auth import get_current_user
from app.services.http_client import http_client
from app.services.livekit_api import generate_livekit_token
from app.services.db import save_interview_session

router = APIRouter(prefix="/api", tags=["tokens", "interview_types"])


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


class InterviewTypeItem(BaseModel):
    id: str = Field(..., description="The internal ID of the interview type", examples=["swe"])
    name: str = Field(..., description="Human-readable name", examples=["Software Engineering"])
    description: str = Field(..., description="Short description of what the interview covers")


class InterviewTypesResponse(BaseModel):
    types: List[InterviewTypeItem] = Field(..., description="List of available interview types")


@router.get(
    "/interview-types",
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


@router.post(
    "/token", 
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

    # Handle dynamic DSA questions passed via interview_type (e.g. "dsa:1,2")
    if payload.interview_type.startswith("dsa:"):
        parts = payload.interview_type.split(":", 1)
        if len(parts) > 1 and parts[1]:
            extracted_ids = [id_str.strip() for id_str in parts[1].split(",") if id_str.strip()]
            if payload.question_ids:
                payload.question_ids.extend(extracted_ids)
            else:
                payload.question_ids = extracted_ids
        payload.interview_type = "dsa"
        
    ai_selected_questions = []
    try:
        if payload.interview_type == "dsa":
            response = await http_client.get(f"{settings.MAIN_SERVICE_URL}/dsa/questions")
            if response.status_code == 200:
                dsa_pool = response.json()
                if payload.question_ids:
                    ai_selected_questions = [q for q in dsa_pool if str(q.get("id")) in payload.question_ids]
                else:
                    ai_selected_questions = random.sample(dsa_pool, min(2, len(dsa_pool)))
        elif payload.interview_type == "system_design":
            url = f"{settings.MAIN_SERVICE_URL}/system-design/questions"
            query_params = {}
            if payload.domain:
                query_params["domain"] = payload.domain
            if payload.role:
                query_params["role"] = payload.role
            
            response = await http_client.get(url, params=query_params)
            if response.status_code == 200:
                sd_pool = response.json()
                if payload.question_ids:
                    ai_selected_questions = [q for q in sd_pool if str(q.get("id")) in payload.question_ids or q.get("id") in payload.question_ids]
                else:
                    ai_selected_questions = random.sample(sd_pool, min(1, len(sd_pool)))
        elif payload.interview_type in ["behavioral", "hr"]:
            response = await http_client.get(f"{settings.MAIN_SERVICE_URL}/behavioral/questions?limit=2")
            if response.status_code == 200:
                ai_selected_questions = response.json()
        elif payload.interview_type in ["product_management", "pm"]:
            response = await http_client.get(f"{settings.MAIN_SERVICE_URL}/pm/questions?limit=2")
            if response.status_code == 200:
                ai_selected_questions = response.json()
        elif payload.interview_type in ["ai_ml", "ml-engineer-infra", "agentic-ai-engineer"]:
            response = await http_client.get(f"{settings.MAIN_SERVICE_URL}/aiml/questions?limit=2")
            if response.status_code == 200:
                ai_selected_questions = response.json()
    except Exception as e:
        # Non-blocking question fetching
        pass

    token = generate_livekit_token(
        identity=username, 
        room_name=payload.room_name, 
        user_id=user_id,
        interview_type=payload.interview_type,
        ai_selected_questions=ai_selected_questions
    )

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
        "url": settings.LIVEKIT_URL or "ws://localhost:7880",
        "roomName": payload.room_name,
        "candidate": username,
        "ai_selected_questions": ai_selected_questions
    }
