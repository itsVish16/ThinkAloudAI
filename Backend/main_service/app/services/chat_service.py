import json
import asyncio
import logging
import time
import os
from typing import List, AsyncGenerator
from fastapi import HTTPException, WebSocket, WebSocketDisconnect
import websockets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, UTC

from app.database import SessionLocal
from app.models.chat import ChatSession, ChatMessageModel
from app.schemas.chat_feature import ChatStreamRequest, ChatMessageOut
from app.agent.chat_agent import agent_executor
from app.config import settings

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from opik.integrations.langchain import OpikTracer

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    async def generate_chat_title(session_id: str, first_message: str) -> str:
        try:
            llm = ChatOpenAI(
                model=settings.FIREWORKS_MODEL,
                base_url=settings.FIREWORKS_BASE_URL,
                api_key=settings.FIREWORKS_API_KEY,
                temperature=0.3
            )
            messages = [
                SystemMessage(content="Generate a short, concise title (max 5 words) for this chat conversation based on the user's first prompt. Do not use quotes, punctuation at the end, or extra text. Just return the title."),
                HumanMessage(content=first_message)
            ]
            result = await llm.ainvoke(messages)
            title = result.content.strip(" \"'")
            
            async with SessionLocal() as db:
                try:
                    session = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
                    session_obj = session.scalars().first()
                    if session_obj:
                        session_obj.title = title
                        await db.commit()
                except Exception as e:
                    await db.rollback()
                    logger.error(f"Error updating chat title in DB: {e}")
            return title
        except Exception as e:
            logger.error(f"Error generating chat title: {e}")
            return None

    @staticmethod
    async def chat_stream_generator(request: ChatStreamRequest, user_id: str, redis_client) -> AsyncGenerator[str, None]:
        session_id = request.session_id
        user_query = request.message

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
                
                # Merge with Redis buffer for this session
                raw_buffer = await redis_client.lrange(f"chat:buffer:{session_id}", 0, -1)
                for raw in raw_buffer:
                    try:
                        msg_data = json.loads(raw)
                        db_messages.append(ChatMessageModel(
                            session_id=session_id,
                            role=msg_data["role"],
                            content=msg_data["content"]
                        ))
                    except Exception:
                        pass
                
                # Also check legacy global buffer if any exists
                legacy_buffer = await redis_client.lrange("chat:buffer", 0, -1)
                for raw in legacy_buffer:
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
                    # Skip custom UI messages that LangChain cannot coerce
                    if msg.role not in ["human", "user", "ai", "assistant", "system", "tool", "function", "developer"]:
                        continue
                        
                    try:
                        parsed_content = json.loads(msg.content)
                        if isinstance(parsed_content, list):
                            history.append((msg.role, parsed_content))
                        else:
                            history.append((msg.role, msg.content))
                    except (json.JSONDecodeError, TypeError):
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

                # 4. Save new user message to per-session Redis buffer
                await redis_client.rpush(f"chat:buffer:{session_id}", json.dumps({
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

                os.environ["OPIK_API_KEY"] = settings.OPIK_API_KEY
                if hasattr(settings, "OPIK_WORKSPACE") and settings.OPIK_WORKSPACE:
                    os.environ["OPIK_WORKSPACE"] = settings.OPIK_WORKSPACE
                if hasattr(settings, "OPIK_PROJECT_NAME") and settings.OPIK_PROJECT_NAME:
                    os.environ["OPIK_PROJECT_NAME"] = settings.OPIK_PROJECT_NAME
                    
                opik_tracer = OpikTracer()

                if is_new_session:
                    new_title = await ChatService.generate_chat_title(session_id, user_query)
                    if new_title:
                        yield f"data: {json.dumps({'type': 'rename_chat', 'title': new_title})}\n\n"

                # Define tool registry for rich frontend rendering
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
                    config={"configurable": {"thread_id": session_id, "user_id": user_id}, "callbacks": [opik_tracer]}
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
                            if "Error creating roadmap" not in str(tool_output):
                                try:
                                    # Robustly extract ID by fetching the latest roadmap for the user
                                    async with SessionLocal() as db_session:
                                        from app.models.roadmap import Roadmap
                                        result = await db_session.execute(
                                            select(Roadmap)
                                            .filter(Roadmap.user_id == user_id)
                                            .order_by(Roadmap.created_at.desc())
                                        )
                                        latest_roadmap = result.scalars().first()
                                        if latest_roadmap:
                                            await redis_client.rpush(f"chat:buffer:{session_id}", json.dumps({
                                                "session_id": session_id,
                                                "role": "roadmap",
                                                "content": str(latest_roadmap.id)
                                            }))
                                            yield f"data: {json.dumps({'type': 'roadmap', 'id': str(latest_roadmap.id)})}\n\n"
                                except Exception as e:
                                    logger.error(f"Error buffering roadmap: {e}")
                                    
                        status = "completed"
                        if "Error creating roadmap" in str(tool_output):
                            status = "failed"
                            
                        yield f"data: {json.dumps({'type': 'tool_end', 'id': run_id, 'tool': name, 'output': str(tool_output), 'status': status, 'time': time.time()})}\n\n"

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
                    await redis_client.rpush(f"chat:buffer:{session_id}", json.dumps({
                        "session_id": session_id,
                        "role": "assistant",
                        "content": assistant_response
                    }))

            except Exception as e:
                await db.rollback()
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    @staticmethod
    async def get_sessions(db: AsyncSession, user_id: str, skip: int, limit: int) -> List[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_session_messages(session_id: str, db: AsyncSession, user_id: str, redis_client) -> List[ChatMessageModel]:
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
        
        # Merge with per-session Redis buffer
        dummy_id = 999999
        raw_buffer = await redis_client.lrange(f"chat:buffer:{session_id}", 0, -1)
        for raw in raw_buffer:
            try:
                msg_data = json.loads(raw)
                db_msgs.append(ChatMessageModel(
                    id=dummy_id,
                    session_id=session_id,
                    role=msg_data["role"],
                    content=msg_data["content"],
                    created_at=datetime.now(UTC)
                ))
                dummy_id += 1
            except Exception:
                pass

        # Also check legacy global buffer if any exists
        legacy_buffer = await redis_client.lrange("chat:buffer", 0, -1)
        for raw in legacy_buffer:
            try:
                msg_data = json.loads(raw)
                if msg_data.get("session_id") == session_id:
                    db_msgs.append(ChatMessageModel(
                        id=dummy_id,
                        session_id=session_id,
                        role=msg_data["role"],
                        content=msg_data["content"],
                        created_at=datetime.now(UTC)
                    ))
                    dummy_id += 1
            except Exception:
                pass
        return db_msgs

    @staticmethod
    async def debug_messages(db: AsyncSession) -> List[dict]:
        result = await db.execute(select(ChatMessageModel).order_by(ChatMessageModel.id.desc()).limit(20))
        msgs = result.scalars().all()
        return [{"id": m.id, "session_id": m.session_id, "role": m.role, "content": m.content[:100]} for m in msgs]

    @staticmethod
    async def delete_session(session_id: str, db: AsyncSession, user_id: str) -> dict:
        result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id))
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        await db.delete(session)
        await db.commit()
        return {"message": f"Session {session_id} successfully deleted"}

    @staticmethod
    async def voice_stream_handler(websocket: WebSocket):
        await websocket.accept()
        
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
                async def forward_audio_to_sm():
                    try:
                        while True:
                            data = await websocket.receive_bytes()
                            await sm_ws.send(data)
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        logger.warning("Error reading from client: %s", e)
                    finally:
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
