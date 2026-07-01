from enum import Enum
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class InterviewStage(str, Enum):
    # Strict 3-step intro flow
    INTRO_AUDIO_CHECK = "intro_audio_check"
    INTRO_AGENDA = "intro_agenda"
    INTRO_CANDIDATE = "intro_candidate"
    
    # Core stages (shared/modular)
    RESUME_PROBE = "resume_probe"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    SYSTEM_DESIGN_CORE = "system_design_core"
    DSA_CORE = "dsa_core"
    BEHAVIORAL_STAR = "behavioral_star"
    PRESENTATION_QA = "presentation_qa"
    AIML_CORE = "ai_ml_core"
    PRODUCT_SENSE_CORE = "product_sense_core"
    
    CANDIDATE_QA = "candidate_qa"
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"

class EvaluationResult(BaseModel):
    score: int = Field(description="Score from 1-5 evaluating the candidate's last answer. 0 if the user just asked a question or dodged.")
    feedback: str = Field(description="Brief internal note on the candidate's performance or behavior in the last turn.")
    objective_met: bool = Field(description="True ONLY IF the interviewer has gathered enough information to complete the current interview stage.")
    next_stage: Optional[InterviewStage] = Field(description="The next stage to transition to, IF objective_met is true.")
    trigger_next_question: bool = Field(default=False, description="Set to True ONLY if the candidate has successfully passed the current coding question and is ready for a new coding problem.")

class InterviewState(TypedDict):
    messages: List[Dict[str, str]]
    stage: str
    candidate_name: str
    resume_summary: str
    evaluations: List[Dict[str, Any]]  # Stores dict representations of EvaluationResult
    stream_queue: Optional[Any]
    
    # Time Awareness and Routing
    start_time: float
    max_duration_minutes: int
    interview_type: str
    
    # Multimodal Visual Context
    latest_visual_context: Optional[str]
    latest_whiteboard_context: Optional[str]
    
    # State containing AI selected questions from API Token
    ai_selected_questions: Optional[List[Dict[str, Any]]]
    active_question_index: int
    
    # Real-time IDE Context
    latest_code: Optional[str]
    latest_execution: Optional[Dict[str, Any]]
