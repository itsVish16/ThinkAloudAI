import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_redis
from app.schemas.chat_feature import ChatStreamRequest, ChatMessageOut, ChatSessionOut
from app.services.chat_service import ChatService
from app.auth import verify_jwt

logger = logging.getLogger(__name__)
router = APIRouter()

def get_current_user_id(payload: dict = Depends(verify_jwt)) -> str:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token payload: 'sub' missing")
    return user_id

@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest, user_id: str = Depends(get_current_user_id), redis_client = Depends(get_redis)):
    return StreamingResponse(
        ChatService.chat_stream_generator(request, user_id, redis_client), 
        media_type="text/event-stream"
    )

@router.get("/sessions", response_model=List[ChatSessionOut])
async def get_sessions(
    db: AsyncSession = Depends(get_db), 
    user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    return await ChatService.get_sessions(db, user_id, skip, limit)

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
async def get_session_messages(
    session_id: str, 
    db: AsyncSession = Depends(get_db), 
    user_id: str = Depends(get_current_user_id), 
    redis_client = Depends(get_redis)
):
    return await ChatService.get_session_messages(session_id, db, user_id, redis_client)

@router.get("/debug/messages")
async def debug_messages(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return await ChatService.debug_messages(db)

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return await ChatService.delete_session(session_id, db, user_id)

@router.websocket("/chat/voice-stream")
async def voice_stream(websocket: WebSocket):
    await ChatService.voice_stream_handler(websocket)
