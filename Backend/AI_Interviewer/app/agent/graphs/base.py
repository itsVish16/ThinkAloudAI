from app.agent.state import InterviewState
from app.agent.prompts import STAGE_PROMPTS, EVALUATION_PROMPT, EVALUATOR_RULES
from app.agent.llm import call_llm, evaluate_llm
import time

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
    if elapsed_minutes >= max_duration - 10:
        time_warning = "WARNING: You only have a few minutes left. Keep questions extremely brief and move towards wrap up."
        
    from datetime import datetime
    
    remaining_minutes = max_duration - elapsed_minutes
    current_date = datetime.now().strftime("%B %d, %Y")

    active_idx = state.get("active_question_index", 0)
    questions = state.get("ai_selected_questions", [])
    active_q = questions[active_idx] if active_idx < len(questions) else None

    prompt = prompt.format(
        elapsed_minutes=elapsed_minutes,
        max_duration_minutes=max_duration,
        remaining_minutes=remaining_minutes,
        current_date=current_date,
        time_warning=time_warning,
        interview_type=state.get("interview_type", "General"),
        ai_selected_questions=questions,
        current_active_question=active_q,
        latest_code=state.get("latest_code", "None yet"),
        latest_execution=state.get("latest_execution", "None yet"),
        latest_whiteboard_context=state.get("latest_whiteboard_context", "No visual data yet")
    )

    
    # Fast streaming call to TTS
    resp = await call_llm(state["messages"], prompt, state.get("stream_queue"))
    
    new_messages = state["messages"] + [{"role": "assistant", "content": resp}]
    return {
        "messages": new_messages
    }

async def evaluate_and_route(state: InterviewState):
    """
    The Manager Node. Evaluates the conversation *after* the speaker has replied.
    Updates the stage and logs evaluations. Runs in background while TTS is playing.
    """
    current_stage = state["stage"]
    
    # If we are already done, just exit
    if current_stage == "completed":
        return {}
        
    # Build evaluation prompt with current stage context
    stage_rule = EVALUATOR_RULES.get(current_stage, "Advance when objective is met.")
    eval_prompt = EVALUATION_PROMPT.format(stage=current_stage, stage_rule=stage_rule)
    
    # Evaluate the conversation
    eval_result = await evaluate_llm(state["messages"], eval_prompt)
    
    # Append the evaluation to our state
    evals = state.get("evaluations", [])
    eval_dict = eval_result.model_dump()
    evals.append(eval_dict)
    
    # Default to current stage
    next_stage = current_stage
    
    # Check time constraints
    start_time = state.get("start_time", time.time())
    elapsed_minutes = int((time.time() - start_time) / 60)
    max_duration = state.get("max_duration_minutes", 60)
    
    # Time forced transition
    if elapsed_minutes >= max_duration:
        next_stage = "wrap_up"
    # Normal transition if objective met
    elif eval_result.objective_met and eval_result.next_stage:
        next_stage = eval_result.next_stage.value
        
    return {
        "evaluations": evals,
        "stage": next_stage
    }
