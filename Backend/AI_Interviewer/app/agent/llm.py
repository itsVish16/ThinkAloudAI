import asyncio
import logging
import os
import time
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.agent.prompts import FAST_BRIDGE_PROMPT

logger = logging.getLogger("llm")

# Fast Responder LLM Client (Ultra-Low Latency, e.g. Fireworks Llama-3.2-3B/8B, Groq, Sarvam fast)
fast_client = AsyncOpenAI(
    api_key=settings.fast_llm_key,
    base_url=settings.fast_llm_url,
)

# Deep Reasoning / Main Evaluator LLM Client (Full context reasoning, AST/code evaluation)
main_client = AsyncOpenAI(
    api_key=settings.main_llm_key,
    base_url=settings.main_llm_url,
)

# Background analysis client (latency not critical, used for post-interview analysis)
analysis_client = AsyncOpenAI(
    api_key=settings.analysis_llm_key,
    base_url=settings.analysis_llm_url,
)

# Legacy client alias
client = main_client


# --- Opik tracing bootstrap ---------------------------------------------------
try:
    import opik
    _opik_api_key = os.getenv("OPIK_API_KEY", "")
    if _opik_api_key:
        opik.configure(api_key=_opik_api_key, workspace=os.getenv("OPIK_WORKSPACE", "default"))
    _track = opik.track
except Exception:
    def _track(**kwargs):
        def _decorator(func):
            return func
        return _decorator
    logger.warning("Opik tracing disabled — OPIK_API_KEY not set or opik not installed.")


async def call_fast_bridge(
    messages: List[Dict[str, str]],
    opik_trace_id: Optional[str] = None,
    metrics: Optional[Any] = None,
) -> tuple[bool, str, List[str]]:
    """
    Executes a fast speculative LLM call to classify the turn and generate
    either a [DIRECT] full short response or a [BRIDGE] conversational filler.
    Returns (is_direct, full_text, tokens).
    """
    start_time = time.time()
    recent = messages[-4:] if len(messages) > 4 else messages
    formatted = [{"role": "system", "content": FAST_BRIDGE_PROMPT}] + recent

    tokens: List[str] = []
    first_token_time = None
    try:
        response = await fast_client.chat.completions.create(
            model=settings.FAST_LLM_MODEL,
            messages=formatted,
            max_tokens=settings.FAST_LLM_MAX_TOKENS,
            temperature=0.3,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    if first_token_time is None:
                        first_token_time = time.time()
                    tokens.append(delta)
    except Exception as e:
        logger.warning(f"Fast LLM bridge unavailable: {e}. Falling back to single-stream mode.")
        return False, "", []

    raw_text = "".join(tokens).strip()
    total_ms = (time.time() - start_time) * 1000
    ttft_ms = ((first_token_time or time.time()) - start_time) * 1000

    if metrics:
        metrics.fast_llm_ttft_ms = round(ttft_ms, 1)
        metrics.fast_llm_total_ms = round(total_ms, 1)
        metrics.fast_llm_output = raw_text

    logger.info(f"⚡ [Fast LLM] TTFT: {ttft_ms:.1f}ms | Total: {total_ms:.1f}ms | Output: '{raw_text}'")

    is_direct = raw_text.startswith("[DIRECT]")
    clean_text = raw_text.replace("[DIRECT]", "").replace("[BRIDGE]", "").strip()
    return is_direct, clean_text, tokens


async def call_llm(
    messages: List[Dict[str, str]],
    system_prompt: str,
    stream_queue: Optional[asyncio.Queue] = None,
    opik_trace_id: Optional[str] = None,
    metrics: Optional[Any] = None,
) -> str:
    """
    Standard single-stream LLM query pushing tokens into stream_queue.
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
        response = await main_client.chat.completions.create(
            model=settings.MAIN_LLM_MODEL,
            messages=formatted_messages,
            temperature=0.4,
            max_tokens=1024,
            stream=True,
        )

        in_thinking = False
        async for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None) or ""
                if not content:
                    continue

                if "<think>" in content or "Thinking Process:" in content:
                    in_thinking = True
                    continue
                if "</think>" in content:
                    in_thinking = False
                    content = content.split("</think>")[-1].strip()
                if in_thinking:
                    continue

                if content:
                    if first_token_time is None:
                        first_token_time = time.time()
                        ttft_ms = (first_token_time - start_time) * 1000
                        logger.info("TTFT ms=%.2f", ttft_ms)

                    full_content.append(content)
                    if stream_queue:
                        await stream_queue.put(content)

        if metrics:
            metrics.main_llm_ttft_ms = round(((first_token_time or time.time()) - start_time) * 1000, 1)
            metrics.main_llm_total_ms = round((time.time() - start_time) * 1000, 1)
            metrics.main_llm_output = "".join(full_content).strip()
    except Exception as e:
        logger.error(f"Main LLM API Error: {e}")
        error_msg = " I'm sorry, I'm having trouble connecting to my brain right now. "
        full_content.append(error_msg)
        if stream_queue:
            await stream_queue.put(error_msg)
    finally:
        if stream_queue:
            await stream_queue.put(None)
        if span:
            span.end(output={"output": "".join(full_content)})

    end_time = time.time()
    logger.info("Main LLM total generation time ms=%.2f", (end_time - start_time) * 1000)
    return "".join(full_content)


async def call_analysis_llm(
    messages: List[Dict[str, str]],
    system_prompt: str,
    opik_trace_id: Optional[str] = None,
) -> str:
    """
    Non-streaming LLM call for background post-interview analysis.
    Uses the dedicated analysis model (Fireworks deepseek) for thorough evaluation.
    """
    formatted_messages = [{"role": "system", "content": system_prompt}] + messages
    start_time = time.time()

    try:
        response = await analysis_client.chat.completions.create(
            model=settings.analysis_llm_model,
            messages=formatted_messages,
            temperature=0.3,
            max_tokens=4096,
            stream=False,
        )
        content = response.choices[0].message.content or ""

        # Strip any <think> reasoning blocks
        import re
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        end_time = time.time()
        logger.info("Analysis LLM total time ms=%.2f", (end_time - start_time) * 1000)
        return content
    except Exception as e:
        logger.error(f"Analysis LLM API Error: {e}")
        raise


async def stream_dual_llm(
    messages: List[Dict[str, str]],
    system_prompt: str,
    stream_queue: Optional[asyncio.Queue] = None,
    opik_trace_id: Optional[str] = None,
    stage: Optional[str] = None,
    metrics: Optional[Any] = None,
) -> str:
    """
    Dual-LLM Speculative Pipeline:
    1. Triggers Fast LLM (<150ms TTFT) and Deep Reasoning LLM in parallel.
    2. Fast LLM emits a natural contextual bridge or completes simple turns instantly.
    3. The stream_queue receives fast tokens immediately, then seamlessly stitches
       Main LLM's deep technical reasoning without audible gaps.
    """
    if not settings.DUAL_LLM_ENABLED:
        return await call_llm(messages, system_prompt, stream_queue, opik_trace_id, metrics=metrics)

    start_time = time.time()
    main_buffer: asyncio.Queue = asyncio.Queue()
    main_full_tokens: List[str] = []
    main_task_error: List[Exception] = []
    main_done = asyncio.Event()
    main_first_token_time = None

    async def _run_main_llm():
        nonlocal main_first_token_time
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages
        try:
            response = await main_client.chat.completions.create(
                model=settings.MAIN_LLM_MODEL,
                messages=formatted_messages,
                temperature=0.4,
                max_tokens=1024,
                stream=True,
            )
            in_thinking = False
            async for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    text_chunk = getattr(delta, "content", None) or ""
                    if not text_chunk:
                        continue

                    if "<think>" in text_chunk or "Thinking Process:" in text_chunk:
                        in_thinking = True
                        continue
                    if "</think>" in text_chunk:
                        in_thinking = False
                        text_chunk = text_chunk.split("</think>")[-1].strip()
                    if in_thinking:
                        continue

                    if text_chunk:
                        if main_first_token_time is None:
                            main_first_token_time = time.time()
                        main_full_tokens.append(text_chunk)
                        await main_buffer.put(text_chunk)
            if metrics:
                metrics.main_llm_ttft_ms = round(((main_first_token_time or time.time()) - start_time) * 1000, 1)
                metrics.main_llm_total_ms = round((time.time() - start_time) * 1000, 1)
                metrics.main_llm_output = "".join(main_full_tokens).strip()
        except Exception as e:
            logger.error(f"Error in background main LLM: {e}")
            main_task_error.append(e)
        finally:
            await main_buffer.put(None)
            main_done.set()

    # Launch Deep Reasoning LLM in the background
    main_task = asyncio.create_task(_run_main_llm())

    # For intro, agenda, and wrap up turns, let Main LLM deliver the full rich persona speech
    skip_fast_bridge = bool(stage and (stage.startswith("intro_") or stage == "wrap_up"))

    if skip_fast_bridge:
        is_direct, clean_bridge = False, ""
    else:
        # Execute Fast Responder LLM
        is_direct, clean_bridge, _ = await call_fast_bridge(messages, opik_trace_id, metrics=metrics)

    spoken_tokens: List[str] = []

    try:
        if is_direct and clean_bridge:
            # Case 1: Purely conversational / confirmation turn
            logger.info(f"⚡ [Dual-LLM] Direct short-circuit response: '{clean_bridge}'")
            if stream_queue:
                await stream_queue.put(clean_bridge + " ")
            spoken_tokens.append(clean_bridge)

            # Cancel background main reasoning task to conserve compute & tokens
            if not main_task.done():
                main_task.cancel()
        else:
            # Case 2: Deep technical turn with bridge
            if clean_bridge:
                logger.info(f"⚡ [Dual-LLM] Injecting Fast Bridge: '{clean_bridge}'")
                bridge_payload = clean_bridge + " "
                if stream_queue:
                    await stream_queue.put(bridge_payload)
                spoken_tokens.append(bridge_payload)

            # Seamlessly stitch the tokens from Main LLM as they become available
            while True:
                token = await main_buffer.get()
                if token is None:
                    break
                if stream_queue:
                    await stream_queue.put(token)
                spoken_tokens.append(token)

    finally:
        if stream_queue:
            await stream_queue.put(None)

    total_time = (time.time() - start_time) * 1000
    final_spoken = "".join(spoken_tokens).strip()
    logger.info(f"🎙️ [Dual-LLM] Total turn completion: {total_time:.1f}ms | Spoken: '{final_spoken[:80]}...'")
    return final_spoken


async def evaluate_llm(
    messages: List[Dict[str, str]],
    system_prompt: str,
    opik_trace_id: Optional[str] = None,
    metrics: Optional[Any] = None,
) -> Any:
    """
    Non-streaming LLM call for background stage evaluation and scoring.
    """
    from app.agent.state import EvaluationResult
    import json
    import re

    formatted_messages = [{"role": "system", "content": system_prompt}] + messages
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
    response = await main_client.chat.completions.create(
        model=settings.MAIN_LLM_MODEL,
        messages=formatted_messages,
        temperature=0.0,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    end_time = time.time()
    eval_latency_ms = (end_time - start_time) * 1000
    logger.info("Evaluation generation time ms=%.2f", eval_latency_ms)

    raw_json = response.choices[0].message.content or ""
    cleaned_json = raw_json.strip()
    match = re.search(r"(\{.*\})", cleaned_json, re.DOTALL)
    if match:
        cleaned_json = match.group(1)

    try:
        result = EvaluationResult.model_validate_json(cleaned_json)
        if metrics:
            metrics.eval_latency_ms = round(eval_latency_ms, 1)
            metrics.eval_reasoning = result.reasoning
            metrics.eval_score = result.score
            metrics.eval_objective_met = result.objective_met
        if span:
            span.end(output={"raw_json": raw_json, "parsed": result.model_dump()})
        return result
    except Exception as e:
        logger.error(f"Failed to parse EvaluationResult: {e}")
        # Robust fallback
        fallback = EvaluationResult(
            reasoning="Fallback evaluation due to parsing error.",
            score=3,
            feedback="Progressing stage.",
            objective_met=True,
            trigger_next_question=False
        )
        if metrics:
            metrics.eval_latency_ms = round(eval_latency_ms, 1)
            metrics.eval_reasoning = fallback.reasoning
            metrics.eval_score = fallback.score
            metrics.eval_objective_met = fallback.objective_met
        if span:
            span.end(output={"error": str(e), "fallback": fallback.model_dump()})
        return fallback
