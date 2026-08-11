from langgraph.graph import StateGraph, END
from app.agent.state import InterviewState, InterviewStage
from app.agent.graphs.base import generate_response

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

def build_graph(interview_type: str):
    workflow = StateGraph(InterviewState)
    workflow.add_node("generate_response", generate_response)
    
    workflow.set_entry_point("generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()
