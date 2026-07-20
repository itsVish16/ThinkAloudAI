from langgraph.graph import StateGraph, END
from app.agent.state import InterviewState, InterviewStage
from app.agent.graphs.base import generate_response
from app.agent.prompts import EVALUATION_PROMPT, EVALUATOR_RULES
from app.agent.llm import evaluate_llm
import time

INTERVIEW_FLOWS = {
    "general": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.RESUME_PROBE.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "system_design": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.SYSTEM_DESIGN_REQUIREMENTS.value,
        InterviewStage.SYSTEM_DESIGN_HLD.value,
        InterviewStage.SYSTEM_DESIGN_DEEP_DIVE.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "dsa": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.INTRO_EDITOR.value,
        InterviewStage.DSA_PRESENTATION.value,
        InterviewStage.DSA_APPROACH.value,
        InterviewStage.DSA_CODING.value,
        InterviewStage.DSA_TESTING.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "hr": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.BEHAVIORAL_QUESTION.value,
        InterviewStage.BEHAVIORAL_FOLLOWUP.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "pm": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.PRODUCT_SENSE_CORE.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "presentation": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.PRESENTATION_QA.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "ai_ml": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.AIML_FUNDAMENTALS.value,
        InterviewStage.AIML_SYSTEM.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ]
}

def get_next_stage(interview_type: str, current_stage: str) -> str:
    flow = INTERVIEW_FLOWS.get(interview_type, INTERVIEW_FLOWS["general"])
    try:
        idx = flow.index(current_stage)
        if idx + 1 < len(flow):
            return flow[idx + 1]
    except ValueError:
        pass
    return InterviewStage.WRAP_UP.value

async def evaluate_and_route(state: InterviewState):
    current_stage = state["stage"]
    i_type = state.get("interview_type", "general")
    
    if current_stage == InterviewStage.COMPLETED.value:
        return {}
        
    turns_in_stage = state.get("turns_in_stage", 0) + 1
        
    stage_rule = EVALUATOR_RULES.get(current_stage, "Advance when objective is met.")
    eval_prompt = EVALUATION_PROMPT.format(
        stage=current_stage, 
        stage_rule=stage_rule,
        turns_in_stage=turns_in_stage,
        latest_code=state.get("latest_code") or "None yet",
        latest_execution=state.get("latest_execution") or "None yet"
    )
    eval_result = await evaluate_llm(state["messages"][-10:], eval_prompt, opik_trace_id=state.get("opik_trace_id"))
    
    evals = state.get("evaluations", [])
    eval_dict = eval_result.model_dump()
    evals.append(eval_dict)
    
    next_stage = current_stage
    should_end = state.get("should_end", False)
    
    # Time Check
    start_time = state.get("start_time", time.time())
    elapsed_minutes = int((time.time() - start_time) / 60)
    max_duration = state.get("max_duration_minutes", 60)
    
    # Safety bounds for turns per stage
    max_turns = 15 if "coding" in current_stage else 8
    
    if elapsed_minutes >= max_duration or eval_dict.get("should_end"):
        next_stage = InterviewStage.WRAP_UP.value
        if current_stage == InterviewStage.WRAP_UP.value:
            should_end = True
    elif eval_result.objective_met or turns_in_stage >= max_turns:
        next_stage = get_next_stage(i_type, current_stage)
        turns_in_stage = 0
        
    return {
        "evaluations": evals,
        "stage": next_stage,
        "turns_in_stage": turns_in_stage,
        "should_end": should_end
    }

def build_graph(interview_type: str):
    workflow = StateGraph(InterviewState)
    workflow.add_node("generate_response", generate_response)
    
    workflow.set_entry_point("generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()
