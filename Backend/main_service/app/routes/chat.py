import json
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db, SessionLocal, get_redis
from app.models.chat import ChatSession, ChatMessageModel
from app.schemas.chat_feature import ChatStreamRequest, ChatMessageOut, ChatSessionOut
from app.agent.chat_agent import agent_executor
from app.config import settings

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)
router = APIRouter()

async def generate_chat_title(session_id: str, first_message: str):
    try:
        import os
        llm = ChatOpenAI(
            model="llama-3.3-70b-versatile",
            base_url="https://api.aimlapi.com/v1",
            api_key=os.environ.get("AIML_API_KEY", os.environ.get("OPENAI_API_KEY", "missing_key")),
            temperature=0.3
        )
        messages = [
            SystemMessage(content="Generate a short, concise title (max 5 words) for this chat conversation based on the user's first prompt. Do not use quotes, punctuation at the end, or extra text. Just return the title."),
            HumanMessage(content=first_message)
        ]
        result = await llm.ainvoke(messages)
        title = result.content.strip(" \"'")
        
        async with SessionLocal() as db:
            session = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
            session_obj = session.scalars().first()
            if session_obj:
                session_obj.title = title
                await db.commit()
                
        return title
    except Exception as e:
        import logging
        logging.error(f"Error generating chat title: {e}")
        return None

def get_current_user_id() -> str:
    return "test_user_id"

@router.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest, user_id: str = Depends(get_current_user_id), redis_client = Depends(get_redis)):
    session_id = request.session_id
    user_query = request.message

    async def event_generator():
        async with SessionLocal() as db:
            try:
                is_new_session = False
                # 1. Fetch or create the ChatSession
                result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id))
                session = result.scalars().first()
                if not session:
                    session = ChatSession(id=session_id, user_id=user_id)
                    db.add(session)
                    await db.commit()
                    await db.refresh(session)
                    is_new_session = True

                # 2. Fetch existing session messages
                msg_result = await db.execute(
                    select(ChatMessageModel)
                    .filter(ChatMessageModel.session_id == session_id)
                    .order_by(ChatMessageModel.id.asc())
                )
                db_messages = list(msg_result.scalars().all())
                
                # Merge with Redis buffer
                raw_buffer = await redis_client.lrange("chat:buffer", 0, -1)
                for raw in raw_buffer:
                    try:
                        msg_data = json.loads(raw)
                        if msg_data.get("session_id") == session_id:
                            db_messages.append(ChatMessageModel(
                                session_id=session_id,
                                role=msg_data["role"],
                                content=msg_data["content"]
                            ))
                    except Exception:
                        pass
                
                history = []
                for msg in db_messages:
                    try:
                        parsed_content = json.loads(msg.content)
                        if isinstance(parsed_content, list):
                            history.append((msg.role, parsed_content))
                        else:
                            history.append((msg.role, msg.content))
                    except json.JSONDecodeError:
                        history.append((msg.role, msg.content))

                # 3. Construct user content
                if request.images and len(request.images) > 0:
                    user_content = [{"type": "text", "text": user_query}]
                    for img in request.images:
                        user_content.append({"type": "image_url", "image_url": {"url": img}})
                    db_content = json.dumps(user_content)
                else:
                    user_content = user_query
                    db_content = user_query

                # 4. Save new user message to Redis buffer
                await redis_client.rpush("chat:buffer", json.dumps({
                    "session_id": session_id,
                    "role": "user",
                    "content": db_content
                }))

                # Inject context
                context_injected_content = user_content
                if isinstance(user_content, str):
                    context_injected_content = f"{user_content}\n\n[System Note: The user's current session_id is '{session_id}'. Use this if you need to call get_user_submissions.]"
                elif isinstance(user_content, list):
                    context_injected_content = user_content + [{"type": "text", "text": f"\n\n[System Note: The user's current session_id is '{session_id}'. Use this if you need to call get_user_submissions.]"}]
                
                inputs = {
                    "messages": history + [("user", context_injected_content)]
                }

                from opik.integrations.langchain import OpikTracer
                import os
                from app.config import settings
                
                os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY
                if hasattr(settings, "OPIK_WORKSPACE") and settings.OPIK_WORKSPACE:
                    os.environ["OPIK_WORKSPACE"] = settings.OPIK_WORKSPACE
                if hasattr(settings, "OPIK_PROJECT_NAME") and settings.OPIK_PROJECT_NAME:
                    os.environ["OPIK_PROJECT_NAME"] = settings.OPIK_PROJECT_NAME
                    
                opik_tracer = OpikTracer()

                if is_new_session:
                    new_title = await generate_chat_title(session_id, user_query)
                    if new_title:
                        yield f"data: {json.dumps({'type': 'rename_chat', 'title': new_title})}\n\n"

                # Define tool registry for rich frontend rendering
                import time
                TOOL_REGISTRY = {
                    "get_dsa_questions": {
                        "title": "Fetch DSA Questions",
                        "icon": "database",
                        "description": "Loading solved problems"
                    },
                    "web_search": {
                        "title": "Search Web",
                        "icon": "globe",
                        "description": "Searching latest information"
                    },
                    "create_user_roadmap": {
                        "title": "Generate Roadmap",
                        "icon": "sparkles",
                        "description": "Building personalized plan"
                    },
                    "get_user_submissions": {
                        "title": "Read Code Progress",
                        "icon": "terminal",
                        "description": "Analyzing past attempts"
                    },
                    "get_current_time": {
                        "title": "Check Time",
                        "icon": "globe",
                        "description": "Getting current local time"
                    }
                }

                # Stream response
                assistant_response = ""
                in_think = False
                stream_buffer = ""
                has_started_writing = False
                
                # Emit execution start
                execution_id = f"exec_{int(time.time()*1000)}"
                yield f"data: {json.dumps({'type': 'execution_start', 'executionId': execution_id, 'time': time.time()})}\n\n"
                
                async for event in agent_executor.astream_events(
                    inputs, 
                    version="v2",
                    config={"configurable": {"thread_id": session_id}, "callbacks": [opik_tracer]}
                ):
                    kind = event["event"]
                    name = event["name"]

                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            token = chunk.content
                            assistant_response += token
                            stream_buffer += token
                            
                            while stream_buffer:
                                if not in_think:
                                    if "<think>" in stream_buffer:
                                        parts = stream_buffer.split("<think>", 1)
                                        if parts[0]:
                                            if not has_started_writing:
                                                has_started_writing = True
                                                yield f"data: {json.dumps({'type': 'writing_start', 'time': time.time()})}\n\n"
                                            yield f"data: {json.dumps({'type': 'text_delta', 'content': parts[0]})}\n\n"
                                        yield f"data: {json.dumps({'type': 'thinking_start', 'time': time.time()})}\n\n"
                                        in_think = True
                                        stream_buffer = parts[1]
                                    elif "<" in stream_buffer:
                                        if "<think>".startswith(stream_buffer[stream_buffer.find("<"):]):
                                            if stream_buffer.find("<") > 0:
                                                if not has_started_writing:
                                                    has_started_writing = True
                                                    yield f"data: {json.dumps({'type': 'writing_start', 'time': time.time()})}\n\n"
                                                yield f"data: {json.dumps({'type': 'text_delta', 'content': stream_buffer[:stream_buffer.find('<')]})}\n\n"
                                                stream_buffer = stream_buffer[stream_buffer.find("<"):]
                                            break
                                        else:
                                            if not has_started_writing:
                                                has_started_writing = True
                                                yield f"data: {json.dumps({'type': 'writing_start', 'time': time.time()})}\n\n"
                                            yield f"data: {json.dumps({'type': 'text_delta', 'content': stream_buffer})}\n\n"
                                            stream_buffer = ""
                                    else:
                                        if not has_started_writing:
                                            has_started_writing = True
                                            yield f"data: {json.dumps({'type': 'writing_start', 'time': time.time()})}\n\n"
                                        yield f"data: {json.dumps({'type': 'text_delta', 'content': stream_buffer})}\n\n"
                                        stream_buffer = ""
                                else:
                                    if "</think>" in stream_buffer:
                                        parts = stream_buffer.split("</think>", 1)
                                        if parts[0]:
                                            yield f"data: {json.dumps({'type': 'thinking_delta', 'content': parts[0]})}\n\n"
                                        yield f"data: {json.dumps({'type': 'thinking_end', 'time': time.time()})}\n\n"
                                        in_think = False
                                        stream_buffer = parts[1]
                                    elif "<" in stream_buffer:
                                        if "</think>".startswith(stream_buffer[stream_buffer.find("<"):]):
                                            if stream_buffer.find("<") > 0:
                                                yield f"data: {json.dumps({'type': 'thinking_delta', 'content': stream_buffer[:stream_buffer.find('<')]})}\n\n"
                                                stream_buffer = stream_buffer[stream_buffer.find("<"):]
                                            break
                                        else:
                                            yield f"data: {json.dumps({'type': 'thinking_delta', 'content': stream_buffer})}\n\n"
                                            stream_buffer = ""
                                    else:
                                        yield f"data: {json.dumps({'type': 'thinking_delta', 'content': stream_buffer})}\n\n"
                                        stream_buffer = ""

                    elif kind == "on_tool_start":
                        tool_input = event["data"].get("input")
                        run_id = event.get("run_id", f"tool_{int(time.time()*1000)}")
                        tool_meta = TOOL_REGISTRY.get(name, {
                            "title": name.replace("_", " ").title(),
                            "icon": "tool",
                            "description": "Executing tool"
                        })
                        yield f"data: {json.dumps({'type': 'tool_start', 'id': run_id, 'tool': tool_meta, 'input': tool_input, 'time': time.time()})}\n\n"

                    elif kind == "on_tool_end":
                        tool_output = event["data"].get("output")
                        run_id = event.get("run_id", "")
                        
                        if name == "create_user_roadmap":
                            import re
                            match = re.search(r"ID (\d+)", str(tool_output))
                            if match:
                                roadmap_id = match.group(1)
                                await redis_client.rpush("chat:buffer", json.dumps({
                                    "session_id": session_id,
                                    "role": "roadmap",
                                    "content": roadmap_id
                                }))
                        yield f"data: {json.dumps({'type': 'tool_end', 'id': run_id, 'tool': name, 'output': str(tool_output), 'time': time.time()})}\n\n"

                if stream_buffer:
                    if in_think:
                        yield f"data: {json.dumps({'type': 'thinking_delta', 'content': stream_buffer})}\n\n"
                    else:
                        if not has_started_writing:
                            has_started_writing = True
                            yield f"data: {json.dumps({'type': 'writing_start', 'time': time.time()})}\n\n"
                        yield f"data: {json.dumps({'type': 'text_delta', 'content': stream_buffer})}\n\n"

                if has_started_writing:
                    yield f"data: {json.dumps({'type': 'writing_end', 'time': time.time()})}\n\n"
                    
                yield f"data: {json.dumps({'type': 'execution_end', 'time': time.time()})}\n\n"

                if assistant_response:
                    await redis_client.rpush("chat:buffer", json.dumps({
                        "session_id": session_id,
                        "role": "assistant",
                        "content": assistant_response
                    }))

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions", response_model=List[ChatSessionOut])
async def get_sessions(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    result = await db.execute(select(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()))
    return result.scalars().all()


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id), redis_client = Depends(get_redis)):
    result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
        
    msg_result = await db.execute(
        select(ChatMessageModel)
        .filter(ChatMessageModel.session_id == session_id)
        .order_by(ChatMessageModel.id.asc())
    )
    db_msgs = list(msg_result.scalars().all())
    
    # Merge with Redis buffer
    raw_buffer = await redis_client.lrange("chat:buffer", 0, -1)
    for raw in raw_buffer:
        try:
            msg_data = json.loads(raw)
            if msg_data.get("session_id") == session_id:
                db_msgs.append(ChatMessageModel(
                    id=999999, # Dummy ID for frontend sorting
                    session_id=session_id,
                    role=msg_data["role"],
                    content=msg_data["content"]
                ))
        except Exception:
            pass
            
    return db_msgs


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
        
    await db.delete(session)
    await db.commit()
    return {"message": f"Session {session_id} successfully deleted"}

from fastapi import WebSocket, WebSocketDisconnect
import websockets

@router.websocket("/chat/voice-stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint that acts as a proxy between the frontend client
    and the Speechmatics Real-Time API for live dictation.
    """
    await websocket.accept()
    
    from app.config import settings
    api_key = settings.SPEECHMATICS_API_KEY
    if not api_key:
        await websocket.send_json({"error": "SPEECHMATICS_API_KEY not configured"})
        await websocket.close()
        return

    # Connect to Speechmatics Real-Time API
    sm_url = "wss://eu2.rt.speechmatics.com/v2"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        async with websockets.connect(sm_url, additional_headers=headers) as sm_ws:
            # 1. Send StartRecognition message
            start_msg = {
                "message": "StartRecognition",
                "audio_format": {
                    "type": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": 16000
                },
                "transcription_config": {
                    "language": "en",
                    "enable_partials": True,
                    "max_delay": 2
                }
            }
            await sm_ws.send(json.dumps(start_msg))
            
            # Wait for RecognitionStarted
            while True:
                msg = await sm_ws.recv()
                msg_data = json.loads(msg)
                if msg_data.get("message") == "RecognitionStarted":
                    break
                elif msg_data.get("message") == "Error":
                    raise Exception(f"Speechmatics Error: {msg_data}")

            # Start concurrent tasks for relaying audio to SM, and SM text back to frontend
            import asyncio
            
            async def forward_audio_to_sm():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        # Send audio chunk
                        await sm_ws.send(data)
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.warning("Error reading from client: %s", e)
                finally:
                    # Notify Speechmatics we're done
                    try:
                        await sm_ws.send(json.dumps({"message": "EndOfStream"}))
                    except Exception:
                        pass
                        
            async def forward_sm_to_client():
                try:
                    async for message in sm_ws:
                        msg_data = json.loads(message)
                        if msg_data.get("message") == "AddPartialTranscript":
                            text = msg_data["metadata"]["transcript"]
                            if text:
                                await websocket.send_json({"type": "partial", "text": text})
                        elif msg_data.get("message") == "AddTranscript":
                            text = msg_data["metadata"]["transcript"]
                            if text:
                                await websocket.send_json({"type": "final", "text": text})
                        elif msg_data.get("message") == "EndOfTranscript":
                            break
                except Exception as e:
                    logger.warning("Error reading from Speechmatics: %s", e)

            await asyncio.gather(
                forward_audio_to_sm(),
                forward_sm_to_client()
            )
            
    except Exception as e:
        logger.warning("Speechmatics connection error: %s", e)
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
