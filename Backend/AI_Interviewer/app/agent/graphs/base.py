from app.agent.state import InterviewState
from app.agent.prompts import STAGE_PROMPTS, TTS_RULES
from app.agent.llm import call_llm
import time
from datetime import datetime

async def generate_response(state: InterviewState):
    """
    The Speaker Node. Purely conversational. Streams a response based on the current stage.
    """
    current_stage = state["stage"]
    prompt = STAGE_PROMPTS.get(current_stage, STAGE_PROMPTS["wrap_up"])
    
    # Calculate time context
    start_time = state.get("start_time", time.time())
    elapsed_minutes = int((time.time() - start_time) / 60)
    max_duration = state.get("max_duration_minutes", 60)
    time_warning = ""
    if elapsed_minutes >= max_duration - 5:
        time_warning = "WARNING: You are out of time. End the interview gracefully in this turn."
        
    remaining_minutes = max_duration - elapsed_minutes
    current_date = datetime.now().strftime("%B %d, %Y")

    active_idx = state.get("active_question_index", 0)
    questions = state.get("ai_selected_questions", [])
    active_q = questions[active_idx] if active_idx < len(questions) else None

    # Format interview_type to make AI greeting more natural
    i_type_raw = state.get("interview_type", "General")
    if "system_design" in i_type_raw.lower() or "sd" in i_type_raw.lower():
        formatted_type = "System Design"
    elif "dsa" in i_type_raw.lower() or "swe" in i_type_raw.lower():
        formatted_type = "Data Structures and Algorithms"
    elif "pm" in i_type_raw.lower() or "product" in i_type_raw.lower():
        formatted_type = "Product Management"
    elif "hr" in i_type_raw.lower() or "behavioral" in i_type_raw.lower():
        formatted_type = "Behavioral"
    elif "ai" in i_type_raw.lower() or "ml" in i_type_raw.lower():
        formatted_type = "AI and Machine Learning"
    else:
        formatted_type = i_type_raw.replace("_", " ").title()

    prompt = prompt.format(
        elapsed_minutes=elapsed_minutes,
        max_duration_minutes=max_duration,
        remaining_minutes=remaining_minutes,
        current_date=current_date,
        time_warning=time_warning,
        interview_type=formatted_type,
        current_active_question=active_q
    )

    from app.agent.prompts import INTERVIEW_PERSONA
    
    # Smarter context injection
    extra_context = ""
    
    # Only inject code context during coding stages
    if current_stage in ["dsa_coding", "dsa_testing"]:
        code = state.get("latest_code", "")
        exec_out = state.get("latest_execution", "")
        if code:
            extra_context += f"\n\nIDE CONTEXT:\n<CANDIDATE_CODE>\n{code}\n</CANDIDATE_CODE>"
        if exec_out:
            extra_context += f"\n<EXECUTION_OUTPUT>\n{exec_out}\n</EXECUTION_OUTPUT>"
            
    # Only inject visual context during design/whiteboarding stages
    if "system_design" in current_stage:
        whiteboard = state.get("latest_whiteboard_context", "")
        if whiteboard and "Visual Context:" not in whiteboard:
            extra_context += f"\n\nWHITEBOARD VISUAL OBSERVATION:\n{whiteboard}"

    full_system_prompt = f"{INTERVIEW_PERSONA}\n\n{TTS_RULES}\n\n{prompt}{extra_context}"
    
    # Adaptive message window
    # Intros don't need much history. Coding needs more.
    if current_stage.startswith("intro_"):
        window_size = 6
    elif current_stage == "wrap_up":
        window_size = 4
    else:
        window_size = 10
        
    recent_messages = state["messages"][-window_size:]
    
    # Fast streaming call to TTS
    resp = await call_llm(recent_messages, full_system_prompt, state.get("stream_queue"), opik_trace_id=state.get("opik_trace_id"))
    
    new_messages = state["messages"] + [{"role": "assistant", "content": resp}]
    return {
        "messages": new_messages
    }
