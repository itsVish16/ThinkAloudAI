from langgraph.graph import StateGraph, END
from app.agent.state import InterviewStage, InterviewState
from app.agent.prompts import STAGE_PROMPTS, EVALUATION_PROMPT, INTERVIEW_PERSONA
from app.agent.llm import call_llm, evaluate_llm

async def generate_response(state: InterviewState):
    """
    The Speaker Node. Purely conversational. Streams a response based on the current stage.
    """
    current_stage = state["stage"]
    stage_template = STAGE_PROMPTS.get(current_stage, STAGE_PROMPTS["wrap_up"])
    
    # 1. Format the stage template safely
    questions = state.get("ai_selected_questions")
    active_idx = state.get("active_question_index", 0)
    current_q = ""
    if questions and isinstance(questions, list) and len(questions) > active_idx:
        q_obj = questions[active_idx]
        if isinstance(q_obj, dict):
            current_q = f"Title: {q_obj.get('title', '')}\nDescription: {q_obj.get('description', '')}"
        else:
            current_q = str(q_obj)
        
    format_kwargs = {
        "interview_type": state.get("interview_type", "technical"),
        "current_active_question": current_q,
    }
    
    try:
        stage_prompt = stage_template.format(**format_kwargs)
    except Exception:
        stage_prompt = stage_template
        
    # 2. Build Conversation Memory from the last 2 evaluations
    evals = state.get("evaluations", [])
    memory_text = "None"
    if evals:
        recent_feedback = [e.get("feedback", "") for e in evals[-2:] if e.get("feedback")]
        if recent_feedback:
            memory_text = " ".join(recent_feedback)
            
    # 3. Add context for code/execution if present (Whiteboard is injected in worker.py directly into user_text)
    latest_code = state.get("latest_code")
    code_ctx = f"\n[Candidate Code Snapshot]:\n{latest_code}\n" if latest_code else ""
    
    latest_exec = state.get("latest_execution")
    exec_ctx = f"\n[Code Execution Result]:\n{latest_exec}\n" if latest_exec else ""
            
    # Combine the three parts
    full_prompt = f"{INTERVIEW_PERSONA}\n\n{stage_prompt}\n{code_ctx}{exec_ctx}\n[CONVERSATION MEMORY (Do not repeat yourself)]:\n{memory_text}"
    
    # Fast streaming call to TTS
    resp = await call_llm(state["messages"], full_prompt, state.get("stream_queue"))
    
    new_messages = state["messages"] + [{"role": "assistant", "content": resp}]
    return {
        "messages": new_messages
    }

from app.agent.prompts import STAGE_PROMPTS, EVALUATION_PROMPT, INTERVIEW_PERSONA, EVALUATOR_RULES
import time

INTERVIEW_FLOWS = {
    "dsa": [
        "intro_audio_check",
        "intro_agenda",
        "intro_candidate",
        "dsa_core",
        "resume_probe",
        "candidate_qa",
        "wrap_up",
        "completed"
    ],
    "system_design": [
        "intro_audio_check",
        "intro_agenda",
        "intro_candidate",
        "resume_probe",
        "system_design_core",
        "candidate_qa",
        "wrap_up",
        "completed"
    ],
    "behavioral": [
        "intro_audio_check",
        "intro_agenda",
        "intro_candidate",
        "behavioral_star",
        "candidate_qa",
        "wrap_up",
        "completed"
    ],
    "general": [
        "intro_audio_check",
        "intro_agenda",
        "intro_candidate",
        "technical_assessment",
        "candidate_qa",
        "wrap_up",
        "completed"
    ]
}

async def evaluate_and_route(state: InterviewState):
    """
    The Manager Node. Evaluates the conversation *after* the speaker has replied.
    Updates the stage deterministically based on INTERVIEW_FLOWS.
    """
    current_stage = state["stage"]
    
    if current_stage == InterviewStage.COMPLETED.value:
        return {}
        
    # Get the specific evaluator rule for this stage
    stage_rule = EVALUATOR_RULES.get(current_stage, "Advance when objective is met.")
    eval_prompt = EVALUATION_PROMPT.format(stage=current_stage, stage_rule=stage_rule)
    
    # Evaluate the conversation
    eval_result = await evaluate_llm(state["messages"], eval_prompt)
    
    # Append the evaluation to our state
    evals = state.get("evaluations", [])
    eval_dict = eval_result.model_dump()
    evals.append(eval_dict)
    
    next_stage = current_stage
    interview_type = state.get("interview_type", "general")
    flow = INTERVIEW_FLOWS.get(interview_type, INTERVIEW_FLOWS["general"])
    
    # Check if objective met to advance deterministically
    if eval_result.objective_met:
        try:
            current_index = flow.index(current_stage)
            if current_index + 1 < len(flow):
                next_stage = flow[current_index + 1]
        except ValueError:
            next_stage = "wrap_up" # fallback
            
    # Time-based override for DSA interviews
    if interview_type == "dsa" and current_stage == "dsa_core":
        start_time = state.get("start_time", time.time())
        max_minutes = state.get("max_duration_minutes", 45)
        elapsed_minutes = (time.time() - start_time) / 60.0
        
        # If in the last 7 minutes, force transition to project discussion
        if max_minutes - elapsed_minutes <= 7.0:
            next_stage = "resume_probe"
            
    return {
        "evaluations": evals,
        "stage": next_stage
    }

workflow = StateGraph(InterviewState)

workflow.add_node("generate_response", generate_response)
workflow.add_node("evaluate_and_route", evaluate_and_route)

# The graph is simple: generate a response, then evaluate what just happened
workflow.set_entry_point("generate_response")
workflow.add_edge("generate_response", "evaluate_and_route")
workflow.add_edge("evaluate_and_route", END)

interview_agent = workflow.compile()