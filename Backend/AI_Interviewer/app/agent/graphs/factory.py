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
        InterviewStage.TECHNICAL_ASSESSMENT.value,
        InterviewStage.BEHAVIORAL_STAR.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "system_design": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.RESUME_PROBE.value,
        InterviewStage.SYSTEM_DESIGN_CORE.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "dsa": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.INTRO_EDITOR.value,
        InterviewStage.DSA_CORE.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "hr": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.RESUME_PROBE.value,
        InterviewStage.BEHAVIORAL_STAR.value,
        InterviewStage.CANDIDATE_QA.value,
        InterviewStage.WRAP_UP.value,
        InterviewStage.COMPLETED.value
    ],
    "pm": [
        InterviewStage.INTRO_AUDIO_CHECK.value,
        InterviewStage.INTRO_AGENDA.value,
        InterviewStage.INTRO_CANDIDATE.value,
        InterviewStage.RESUME_PROBE.value,
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
        InterviewStage.RESUME_PROBE.value,
        InterviewStage.AIML_CORE.value,
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

def build_graph(interview_type: str):
    async def evaluate_and_route(state: InterviewState):
        current_stage = state["stage"]
        i_type = state.get("interview_type", interview_type)
        
        if current_stage == InterviewStage.COMPLETED.value:
            return {}
            
        stage_rule = EVALUATOR_RULES.get(current_stage, "Advance when objective is met.")
        eval_prompt = EVALUATION_PROMPT.format(stage=current_stage, stage_rule=stage_rule)
        eval_result = await evaluate_llm(state["messages"], eval_prompt)
        
        evals = state.get("evaluations", [])
        eval_dict = eval_result.model_dump()
        evals.append(eval_dict)
        
        next_stage = current_stage
        
        # Time Check
        start_time = state.get("start_time", time.time())
        elapsed_minutes = int((time.time() - start_time) / 60)
        max_duration = state.get("max_duration_minutes", 60)
        
        if elapsed_minutes >= max_duration:
            next_stage = InterviewStage.WRAP_UP.value
        elif eval_result.objective_met:
            # We use our static flows instead of trusting the LLM to pick the right enum randomly
            next_stage = get_next_stage(i_type, current_stage)
            
        return {
            "evaluations": evals,
            "stage": next_stage
        }

    workflow = StateGraph(InterviewState)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("evaluate_and_route", evaluate_and_route)
    
    workflow.set_entry_point("generate_response")
    workflow.add_edge("generate_response", "evaluate_and_route")
    workflow.add_edge("evaluate_and_route", END)
    
    return workflow.compile()
