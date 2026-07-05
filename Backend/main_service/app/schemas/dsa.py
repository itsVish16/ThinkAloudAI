from pydantic import BaseModel, ConfigDict
import datetime
from typing import Optional

class DSAQuestionBase(BaseModel):
    title: str
    description: str
    difficulty: str
    test_cases: str # Stored as JSON string
    python_starter_code: Optional[str] = None
    cpp_starter_code: Optional[str] = None
    cpp_test_harness: Optional[str] = None
    function_name: Optional[str] = "solution"
    hints: Optional[str] = None
    optimal_time_complexity: Optional[str] = None
    optimal_space_complexity: Optional[str] = None

class DSAQuestionCreate(DSAQuestionBase):
    pass

class DSAQuestionOut(DSAQuestionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime.datetime

class CodeSubmitRequest(BaseModel):
    session_id: str
    code: str
    language: str = "python"

class CodeSubmitResponse(BaseModel):
    status: str
    passed_tests: int
    total_tests: int
    error_message: Optional[str] = None
    execution_time_ms: float

class CodeSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: str
    question_id: int
    code: str
    language: str
    status: str
    error_message: Optional[str]
    is_submission: bool
    created_at: datetime.datetime

class UserProblemStatusOut(BaseModel):
    question_id: int
    status: str
    best_runtime_ms: Optional[float] = None
    best_memory_kb: Optional[float] = None
    last_attempted_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class RecommendationOut(BaseModel):
    id: int
    user_id: str
    recommended_item_type: str
    recommended_item_id: int
    reason: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
