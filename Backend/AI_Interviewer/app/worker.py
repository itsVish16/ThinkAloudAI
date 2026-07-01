import asyncio
import json
import logging
import time
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import speechmatics, silero, cartesia
from livekit.plugins.speechmatics import TurnDetectionMode

from app.agent.graphs.factory import build_graph
from app.agent.state import InterviewStage
from app.services.db import get_interview_session, save_interview_session
from app.services.events import publish_interview_completed

load_dotenv(".env.local", override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("interview_worker")

async def queue_generator(queue: asyncio.Queue):
    """
    Helper async generator that yields chunks from the queue until it receives None.
    """
    while True:
        token = await queue.get()
        if token is None:
            break
        yield token

class InterviewAgent(Agent):
    def __init__(self, room, room_id: str, candidate_name: str, user_id: str, interview_type: str, ai_selected_questions: list = None, session_data: dict = None):
        super().__init__(
            instructions="AI Interviewer Agent",
            allow_interruptions=True,
            min_endpointing_delay=2.0
        )
        self.room = room
        self.room_id = room_id
        self.candidate_name = candidate_name
        self.user_id = user_id
        self.interview_type = interview_type
        self.ai_selected_questions = ai_selected_questions or []
        
        # Build the dynamic graph based on the interview type
        self.interview_agent = build_graph(self.interview_type)

        logger.info(f"Initializing InterviewAgent for room: {self.room_id}, candidate: {self.candidate_name}, user_id: {self.user_id}")

        if session_data:
            self.state = session_data["state_data"]
            logger.info(f"Loaded existing session state. Current stage: {self.state['stage']}")
        else:
            self.state = {
                "messages": [],
                "stage": InterviewStage.INTRO_AUDIO_CHECK.value,
                "candidate_name": self.candidate_name,
                "resume_summary": None,
                "evaluations": [],
                "start_time": time.time(),
                "max_duration_minutes": 50,
                "interview_type": self.interview_type,
                "latest_visual_context": None,
                "ai_selected_questions": self.ai_selected_questions,
                "active_question_index": 0,
                "latest_code": None,
                "latest_execution": None,
                "latest_whiteboard_context": None
            }
            logger.info("Created new session state starting with introduction stage.")

        # Real-time state that gets injected before ainvoke
        self.latest_code = self.state.get("latest_code")
        self.latest_execution = self.state.get("latest_execution")
        
        # If we didn't get questions from the participant metadata token, 
        # try to fallback to the existing state (if resuming a session).
        if not self.ai_selected_questions:
            self.ai_selected_questions = self.state.get("ai_selected_questions") or []

    async def on_user_turn_completed(self, turn_ctx, new_message):
        import time
        turn_start_time = time.time()
        
        user_text = new_message.text_content
        logger.info(f"User finished speaking. Raw text: '{user_text}'")

        if not user_text or not user_text.strip():
            logger.info("User text is empty or only whitespace. Ignoring turn.")
            return

        whiteboard_context = self.state.get("latest_whiteboard_context")
        if whiteboard_context and "Visual Context: Camera is on" not in whiteboard_context and "Model not loaded" not in whiteboard_context and "Failed to process" not in whiteboard_context:
            user_text = f"[Candidate Whiteboard Observation: {whiteboard_context}]\n" + user_text
            self.state["latest_whiteboard_context"] = None

        visual_context = self.state.get("latest_visual_context")
        if visual_context and "Visual Context: Camera is on" not in visual_context and "Model not loaded" not in visual_context and "Failed to process" not in visual_context:
            user_text = f"[Candidate Visual Observation: {visual_context}]\nCandidate says: {user_text}"
            self.state["latest_visual_context"] = None
            
        self.state["messages"].append({"role": "user", "content": user_text})
        
        # Setup streaming queue
        queue = asyncio.Queue()
        self.state["stream_queue"] = queue

        pre_graph_time = time.time()
        print(f"⏱️ [Pipeline] STT → Handler overhead: {(pre_graph_time - turn_start_time) * 1000:.2f} ms")

        # Start playing audio from the queue immediately
        speech_handle = self.session.say(queue_generator(queue))

        try:
            # Inject latest async state variables before calling LangGraph
            self.state["latest_code"] = self.latest_code
            self.state["latest_execution"] = self.latest_execution
            self.state["ai_selected_questions"] = self.ai_selected_questions

            # Run state graph (this streams LLM tokens into the queue)
            updated_state = await self.interview_agent.ainvoke(self.state)
            self.state = updated_state
            
            evals = self.state.get("evaluations", [])
            if evals and evals[-1].get("trigger_next_question"):
                logger.info("Evaluator triggered NEXT QUESTION! Sending DataChannel message...")
                
                # Increment active question index
                current_idx = self.state.get("active_question_index", 0)
                if current_idx < len(self.ai_selected_questions) - 1:
                    self.state["active_question_index"] = current_idx + 1

                payload = json.dumps({"type": "next_question"})
                await self.room.local_participant.publish_data(payload.encode("utf-8"))
            
            graph_end_time = time.time()
            print(f"⏱️ [Pipeline] Total Graph/LLM Pipeline Time: {(graph_end_time - turn_start_time) * 1000:.2f} ms")
            
            logger.info(f"Graph execution completed. Next stage: {self.state['stage']}")
            
            # Prepare state copy without the non-serializable queue for SQLite persistence
            state_to_save = self.state.copy()
            state_to_save.pop("stream_queue", None)

            await save_interview_session(
                self.room_id,
                self.user_id,
                self.candidate_name,
                self.state["stage"],
                None,
                state_to_save
            )
            
            if self.state["stage"] == "completed" or self.state["stage"] == InterviewStage.COMPLETED.value:
                # Trigger Background Analysis
                from app.services.analysis import analyze_and_save_interview
                asyncio.create_task(
                    analyze_and_save_interview(
                        session_id=self.room_id,
                        user_id=self.user_id,
                        candidate_name=self.candidate_name,
                        interview_type=self.interview_type,
                        messages=self.state["messages"]
                    )
                )

            # Wait for playback completion
            await speech_handle
            
            playback_end_time = time.time()
            print(f"⏱️ [Pipeline] Total Turn (incl. TTS playback): {(playback_end_time - turn_start_time) * 1000:.2f} ms")
            print(f"⏱️ [Pipeline] TTS Playback Time (after LLM done): {(playback_end_time - graph_end_time) * 1000:.2f} ms")

        except asyncio.CancelledError:
            logger.info("Agent turn was interrupted by the user! Cancelling generation...")
            # Unblock the queue_generator so TTS stops waiting
            await queue.put(None)
            # Try to interrupt the speech playback immediately
            if hasattr(speech_handle, "interrupt"):
                speech_handle.interrupt()
            raise

async def entrypoint(ctx: agents.JobContext):
    logger.info(f"Worker received job request. Room name: {ctx.room.name}, Room ID: {ctx.room.sid}")
    await ctx.connect()
    logger.info("Connected to room.")

    # Extract candidate metadata from the remote participant tokens in the room
    candidate_name = "Candidate"
    user_id = "Unknown"
    interview_type = "general"

    ai_selected_questions = []

    for participant in ctx.room.remote_participants.values():
        candidate_name = participant.name or participant.identity
        user_id = "Unknown"
        interview_type = "general"
        participant_metadata = participant.metadata or "{}"
        logger.info(f"Inspecting participant: name={participant.name}, identity={participant.identity}, metadata={participant.metadata}")
        try:
            meta = json.loads(participant_metadata)
            user_id = meta.get("user_id") or "Unknown"
            candidate_name = meta.get("candidate_name") or candidate_name
            interview_type = meta.get("interview_type") or "general"
            ai_selected_questions = meta.get("ai_selected_questions") or []
        except Exception as e:
            logger.warning(f"Failed to parse participant metadata: {e}")
        break

    logger.info(f"Extracted metadata: candidate_name={candidate_name}, user_id={user_id}, interview_type={interview_type}, questions={len(ai_selected_questions)}")

    stt = speechmatics.STT(
        turn_detection_mode=TurnDetectionMode.ADAPTIVE,
        end_of_utterance_silence_trigger=0.5,
    )
    # Speechmatics TTS - real-time streaming audio
    tts = speechmatics.TTS()
    # Prewarm the WebSocket connection so it's ready immediately
    # tts.prewarm() # removed, speechmatics TTS doesn't seem to have prewarm, or I will let it just be tts = speechmatics.TTS()
    vad = silero.VAD.load()

    session = AgentSession(
        stt=stt,
        tts=tts,
        vad=vad,
    )

    @session.on("metrics_collected")
    def on_metrics_collected(ev):
        m = ev.metrics
        metric_type = type(m).__name__
        if hasattr(m, "ttft"):
            print(f"📊 [{metric_type}] TTFT: {m.ttft:.3f}s")
        if hasattr(m, "stt_latency"):
            print(f"📊 [{metric_type}] STT Latency: {m.stt_latency:.3f}s")
        if hasattr(m, "tts_latency"):
            print(f"📊 [{metric_type}] TTS Latency: {m.tts_latency:.3f}s")

    # Load session data asynchronously before initializing agent
    session_data = await get_interview_session(ctx.room.name)
    
    agent = InterviewAgent(
        room=ctx.room,
        room_id=ctx.room.name,
        candidate_name=candidate_name,
        user_id=user_id,
        interview_type=interview_type,
        ai_selected_questions=ai_selected_questions,
        session_data=session_data
    )
    
    # If it's a new session, save initial state to DB
    if not session_data:
        await save_interview_session(
            agent.room_id,
            agent.user_id,
            agent.candidate_name,
            agent.state["stage"],
            None,
            agent.state
        )

    async def video_processing_task(track, agent_instance, is_whiteboard=False):
        from livekit.rtc import VideoStream
        from app.services.vision import get_vlm_service
        import time
        
        vlm_service = get_vlm_service()
        
        # We use from_track or just instantiate VideoStream. 
        # Typically VideoStream(track) is valid in livekit-python.
        stream = VideoStream(track)
        last_process_time = 0
        
        logger.info(f"Started consuming video frames... (Whiteboard: {is_whiteboard})")
        try:
            async for event in stream:
                now = time.time()
                # Process a frame every 3 seconds
                if now - last_process_time > 3.0:
                    last_process_time = now
                    frame = event.frame
                    description = await vlm_service.analyze_frame(frame, is_whiteboard=is_whiteboard)
                    if is_whiteboard:
                        agent_instance.state["latest_whiteboard_context"] = description
                        logger.debug(f"Updated whiteboard context: {description}")
                    else:
                        agent_instance.state["latest_visual_context"] = description
                        logger.debug(f"Updated visual context: {description}")
        except Exception as e:
            logger.error(f"Video processing task failed: {e}")

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant):
        logger.info(f"Participant connected: {participant.identity}")
        
        # We can extract the metadata from the participant if they injected it.
        try:
            meta = json.loads(participant.metadata or "{}")
            if meta:
                if meta.get("ai_selected_questions"):
                    agent.ai_selected_questions = meta["ai_selected_questions"]
                    logger.info(f"Updated ai_selected_questions from late-joining participant metadata. Total questions: {len(meta['ai_selected_questions'])}")
                    # Inject it into state immediately
                    agent.state["ai_selected_questions"] = agent.ai_selected_questions
        except Exception as e:
            logger.error(f"Failed to parse participant metadata: {e}")

    @ctx.room.on("participant_metadata_changed")
    def on_participant_metadata_changed(participant, old_metadata):
        logger.info(f"Participant metadata changed for: {participant.identity}")
        
        try:
            meta = json.loads(participant.metadata or "{}")
            if meta and meta.get("ai_selected_questions"):
                # If we received new questions, update the agent and its state dynamically!
                agent.ai_selected_questions = meta["ai_selected_questions"]
                agent.state["ai_selected_questions"] = agent.ai_selected_questions
                logger.info(f"Dynamically updated ai_selected_questions from metadata sync! Total questions: {len(agent.ai_selected_questions)}")
        except Exception as e:
            logger.error(f"Failed to parse updated participant metadata: {e}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        from livekit import rtc
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            if publication.source == rtc.TrackSource.SOURCE_SCREEN_SHARE:
                logger.info("Screen share track subscribed! Starting background whiteboard vision task.")
                asyncio.create_task(video_processing_task(track, agent, is_whiteboard=True))
            else:
                logger.info("Video track subscribed! Starting background vision task.")
                asyncio.create_task(video_processing_task(track, agent, is_whiteboard=False))

    @ctx.room.on("data_received")
    def on_data_received(data_packet):
        try:
            payload = data_packet.data.decode("utf-8")
            msg = json.loads(payload)
            msg_type = msg.get("type")
            
            if msg_type == "code_update":
                agent.latest_code = msg.get("code")
                logger.info("Received candidate code update.")
            elif msg_type == "code_execution":
                agent.latest_execution = msg.get("execution")
                logger.info(f"Received candidate code execution result.")
        except Exception as e:
            logger.error(f"Error parsing data packet: {e}")

    async def interview_timer_task(room, duration_minutes):
        logger.info(f"Started {duration_minutes} minute interview timer.")
        await asyncio.sleep(duration_minutes * 60)
        logger.warning(f"Interview time of {duration_minutes} minutes is up! Disconnecting room.")
        await room.disconnect()

    logger.info("Starting AgentSession...")
    asyncio.create_task(interview_timer_task(ctx.room, agent.state["max_duration_minutes"]))
    
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(text_enabled=False),
    )
    logger.info("AgentSession started successfully.")

    # Greets the user immediately if it's a new session
    if not agent.state["messages"]:
        logger.info("Session is new (no messages). Waiting 1.5 seconds for client connection stability...")
        await asyncio.sleep(1.5)
        logger.info("Generating initial greeting...")
        queue = asyncio.Queue()
        agent.state["stream_queue"] = queue
        speech_handle = session.say(queue_generator(queue))

        # Seed with a user message so Gemini API has non-empty contents
        agent.state["messages"].append({"role": "user", "content": f"Hi, I am {candidate_name} and I am ready to start the interview."})

        agent.state["ai_selected_questions"] = agent.ai_selected_questions
        agent.state["latest_code"] = agent.latest_code
        agent.state["latest_execution"] = agent.latest_execution

        updated_state = await agent.interview_agent.ainvoke(agent.state)
        agent.state = updated_state
        
        # Prepare state copy without the non-serializable queue for SQLite persistence
        state_to_save = agent.state.copy()
        state_to_save.pop("stream_queue", None)

        await save_interview_session(
            agent.room_id,
            agent.user_id,
            agent.candidate_name,
            agent.state["stage"],
            None,
            state_to_save
        )
        await speech_handle
    else:
        logger.info(f"Session is already existing with {len(agent.state['messages'])} messages.")
        # If the last message was from the assistant, replay it so the user knows we are connected
        assistant_messages = [msg for msg in agent.state["messages"] if msg["role"] == "assistant"]
        if assistant_messages:
            last_resp = assistant_messages[-1]["content"]
            logger.info("Waiting 1.5 seconds for client connection stability before replay...")
            await asyncio.sleep(1.5)
            logger.info(f"Replaying last assistant response: '{last_resp}'")
            await session.say(last_resp)

if __name__ == "__main__":
    # Pre-load the VLM model into memory globally before the event loop starts
    from app.services.vision import get_vlm_service
    get_vlm_service()
    
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )