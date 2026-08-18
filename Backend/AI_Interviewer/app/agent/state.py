from enum import Enum
from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class InterviewStage(str, Enum):
    # Strict intro flow
    INTRO_AUDIO_CHECK = "intro_audio_check"
    INTRO_AGENDA = "intro_agenda"
    INTRO_CANDIDATE = "intro_candidate"
    INTRO_EDITOR = "intro_editor"
    
    # DSA stages
    DSA_PRESENTATION = "dsa_presentation"
    DSA_APPROACH = "dsa_approach"
    DSA_CODING = "dsa_coding"
    DSA_TESTING = "dsa_testing"
    
    # System Design sub-stages
    SYSTEM_DESIGN_REQUIREMENTS = "system_design_requirements"
    SYSTEM_DESIGN_HLD = "system_design_hld"
    SYSTEM_DESIGN_DEEP_DIVE = "system_design_deep_dive"
    
    # Behavioral sub-stages
    BEHAVIORAL_QUESTION = "behavioral_question"
    BEHAVIORAL_FOLLOWUP = "behavioral_followup"
    
    # AI/ML sub-stages
    AIML_FUNDAMENTALS = "aiml_fundamentals"
    AIML_SYSTEM = "aiml_system"
    
    # Product Management sub-stages
    PM_PROBLEM_FRAMING = "pm_problem_framing"
    PM_USER_SEGMENTATION = "pm_user_segmentation"
    PM_SOLUTION_BRAINSTORMING = "pm_solution_brainstorming"
    PM_METRICS_AND_EXECUTION = "pm_metrics_and_execution"
    
    # Legacy stages kept for backward compatibility / migration
    RESUME_PROBE = "resume_probe"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    SYSTEM_DESIGN_CORE = "system_design_core"
    BEHAVIORAL_STAR = "behavioral_star"
    PRESENTATION_QA = "presentation_qa"
    AIML_CORE = "ai_ml_core"
    PRODUCT_SENSE_CORE = "product_sense_core"
    
    CANDIDATE_QA = "candidate_qa"
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"

class EvaluationResult(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning for the evaluation.")
    score: int = Field(description="Score from 1-5 evaluating the candidate's last answer. 0 if the user just asked a question or dodged.")
    feedback: str = Field(description="Brief internal note on the candidate's performance or behavior in the last turn.")
    objective_met: bool = Field(description="True ONLY IF the interviewer has gathered enough information to complete the current interview stage.")
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
    
    # Stage-level turn counter (reset on stage change)
    turns_in_stage: int
    
    # Self-termination flag — set by evaluator or time logic
    should_end: bool
    
    # Multimodal Visual Context
    latest_visual_context: Optional[str]
    latest_whiteboard_context: Optional[str]
    
    # State containing AI selected questions from API Token
    ai_selected_questions: Optional[List[Dict[str, Any]]]
    active_question_index: int
    
    # Real-time IDE Context
    latest_code: Optional[str]
    latest_execution: Optional[Dict[str, Any]]
    
    # Non-polluting System Nudges (silence monitor / execution status)
    system_prompt_nudges: Optional[List[str]]
    
    # Observability
    opik_trace_id: Optional[str]
