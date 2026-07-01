from langgraph.graph import StateGraph, END
from app.agent.state import InterviewStage, InterviewState
from app.agent.prompts import STAGE_PROMPTS, EVALUATION_PROMPT
from app.agent.llm import call_llm, evaluate_llm

async def generate_response(state: InterviewState):
    """
    The Speaker Node. Purely conversational. Streams a response based on the current stage.
    Extremely fast TTFT.
    """
    current_stage = state["stage"]
    prompt = STAGE_PROMPTS.get(current_stage, STAGE_PROMPTS["wrap_up"])
    
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
    if current_stage == InterviewStage.COMPLETED.value:
        return {}
        
    # Build evaluation prompt with current stage context
    eval_prompt = EVALUATION_PROMPT.format(stage=current_stage)
    
    # Evaluate the conversation
    eval_result = await evaluate_llm(state["messages"], eval_prompt)
    
    # Append the evaluation to our state
    evals = state.get("evaluations", [])
    eval_dict = eval_result.model_dump()
    evals.append(eval_dict)
    
    next_stage = current_stage
    
    # If the LLM decided the objective is met, transition to the next stage it selected
    if eval_result.objective_met and eval_result.next_stage:
        next_stage = eval_result.next_stage.value
        
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