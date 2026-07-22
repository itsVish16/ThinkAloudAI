import asyncio
import logging
import os
import time
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger("llm")

# Initialize AsyncOpenAI client (works with any OpenAI-compatible API: Gemini, Groq, Featherless)
client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY or "dummy_key_not_set",
    base_url=settings.LLM_BASE_URL
)

# --- Opik tracing bootstrap ---------------------------------------------------
# Opik is optional in dev; if it isn't configured we degrade to a no-op tracer
# so the service still runs. In prod the OPIK_API_KEY env is always set.
try:
    import opik
    _opik_api_key = os.getenv("OPIK_API_KEY", "")
    if _opik_api_key:
        opik.configure(api_key=_opik_api_key, workspace=os.getenv("OPIK_WORKSPACE", "default"))
    _track = opik.track
except Exception:  # opik not installed / not configured
    def _track(**kwargs):
        def _decorator(func):
            return func
        return _decorator
    logger.warning("Opik tracing disabled — OPIK_API_KEY not set or opik not installed.")


async def call_llm(messages: List[Dict[str, str]], system_prompt: str, stream_queue: asyncio.Queue = None, opik_trace_id: str = None) -> str:
    """
    Queries the configured LLM endpoint with streaming, pushing tokens
    into the provided queue for real-time TTS generation.
    """
    formatted_messages = [{"role": "system", "content": system_prompt}] + messages
    
    start_time = time.time()
    
    full_content = []
    first_token_time = None
    
    span = None
    try:
        import opik
        if opik_trace_id:
            trace = opik.Trace(id=opik_trace_id)
            span = trace.span(name="interview_call_llm", type="llm", input={"messages": messages, "system_prompt": system_prompt})
    except Exception:
        pass
        
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=formatted_messages,
            temperature=0.4,
            stream=True,
        )
        
        async for chunk in response:
            if chunk.choices:
                content = chunk.choices[0].delta.content or ""
                if content:
                    if first_token_time is None:
                        first_token_time = time.time()
                        logger.info("TTFT ms=%.2f", (first_token_time - start_time) * 1000)

                    full_content.append(content)
                    if stream_queue:
                        await stream_queue.put(content)
    except Exception as e:
        logger.error(f"LLM API Error: {e}")
        error_msg = " I'm sorry, I'm having trouble connecting to my brain right now. "
        full_content.append(error_msg)
        if stream_queue:
            await stream_queue.put(error_msg)
    finally:
        if stream_queue:
            await stream_queue.put(None)  # Signal end of stream for the consumer generator
            
        if span:
            span.end(output={"output": "".join(full_content)})

    end_time = time.time()
    logger.info("LLM total generation time ms=%.2f", (end_time - start_time) * 1000)

    return "".join(full_content)

async def evaluate_llm(messages: List[Dict[str, str]], system_prompt: str, opik_trace_id: str = None) -> Any:
    """
    Non-streaming LLM call for background evaluation. Returns a parsed EvaluationResult.
    """
    from app.agent.state import EvaluationResult
    import json
    
    formatted_messages = [{"role": "system", "content": system_prompt}] + messages
    
    # Force the model to output JSON that matches our Pydantic schema
    schema_str = EvaluationResult.model_json_schema()
    formatted_messages[0]["content"] += f"\n\nJSON SCHEMA:\n{json.dumps(schema_str, indent=2)}"
    
    span = None
    try:
        import opik
        if opik_trace_id:
            trace = opik.Trace(id=opik_trace_id)
            span = trace.span(name="interview_evaluate_llm", type="llm", input={"messages": messages, "system_prompt": system_prompt})
    except Exception:
        pass
        
    start_time = time.time()
    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=formatted_messages,
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    end_time = time.time()
    logger.info("Evaluation generation time ms=%.2f", (end_time - start_time) * 1000)
    
    raw_json = response.choices[0].message.content
    try:
        result = EvaluationResult.model_validate_json(raw_json)
        if span:
            span.end(output={"raw_json": raw_json, "parsed": result.model_dump()})
        return result
    except Exception as e:
        logger.error(f"Failed to parse EvaluationResult: {e}")
        # Return a safe fallback
        fallback = EvaluationResult(
            reasoning=f"Parse Error: {e}",
            score=0,
            feedback="",
            objective_met=False,
            trigger_next_question=False
        )
        if span:
            span.end(output={"error": str(e)})
        return fallback
