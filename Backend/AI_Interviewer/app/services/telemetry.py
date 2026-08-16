import logging
import os
import time
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger("telemetry")

_opik_client = None

def get_opik_client():
    global _opik_client
    if _opik_client is not None:
        return _opik_client
    
    api_key = (settings.OPIK_API_KEY or os.getenv("OPIK_API_KEY", "")).strip()
    if api_key and not api_key.startswith("<"):
        try:
            import opik
            opik.configure(
                api_key=api_key,
                workspace=settings.OPIK_WORKSPACE or "default"
            )
            _opik_client = opik.Opik(project_name=settings.OPIK_PROJECT_NAME or "ThinkAloud.ai")
            logger.info(f"✅ Opik Telemetry initialized for project '{settings.OPIK_PROJECT_NAME}' (workspace: '{settings.OPIK_WORKSPACE}')")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Opik client: {e}")
            _opik_client = None
    return _opik_client


class TurnMetrics:
    def __init__(
        self,
        room_id: str,
        user_id: str,
        candidate_name: str,
        interview_type: str,
        stage: str,
        turn_number: int,
        user_text: str,
    ):
        self.room_id = room_id
        self.user_id = user_id
        self.candidate_name = candidate_name
        self.interview_type = interview_type
        self.stage = stage
        self.turn_number = turn_number
        self.user_text = user_text

        self.turn_start_time = time.time()
        self.stt_received_time = self.turn_start_time
        self.fast_llm_start_time: Optional[float] = None
        self.fast_llm_ttft_ms: Optional[float] = None
        self.fast_llm_total_ms: Optional[float] = None
        self.fast_llm_output: Optional[str] = None

        self.main_llm_start_time: Optional[float] = None
        self.main_llm_ttft_ms: Optional[float] = None
        self.main_llm_total_ms: Optional[float] = None
        self.main_llm_output: Optional[str] = None

        self.first_audio_byte_time: Optional[float] = None
        self.playback_end_time: Optional[float] = None
        self.response_text: str = ""

        # Evaluator metrics
        self.eval_reasoning: Optional[str] = None
        self.eval_score: Optional[int] = None
        self.eval_objective_met: Optional[bool] = None
        self.eval_latency_ms: Optional[float] = None

    def record_first_audio_byte(self):
        if self.first_audio_byte_time is None:
            self.first_audio_byte_time = time.time()

    def record_turn_completed(self, response_text: str):
        self.playback_end_time = time.time()
        self.response_text = response_text
        self._log_console_dashboard()
        self._push_to_opik()

    @property
    def e2e_response_latency_ms(self) -> float:
        if self.first_audio_byte_time:
            return round((self.first_audio_byte_time - self.turn_start_time) * 1000, 1)
        return round((time.time() - self.turn_start_time) * 1000, 1)

    @property
    def total_turn_duration_ms(self) -> float:
        end = self.playback_end_time or time.time()
        return round((end - self.turn_start_time) * 1000, 1)

    def _log_console_dashboard(self):
        fast_ttft_str = f"{self.fast_llm_ttft_ms:.0f} ms" if self.fast_llm_ttft_ms else "Skipped / N/A"
        main_ttft_str = f"{self.main_llm_ttft_ms:.0f} ms" if self.main_llm_ttft_ms else "N/A"
        e2e_str = f"{self.e2e_response_latency_ms:.0f} ms"
        total_dur_str = f"{self.total_turn_duration_ms:.0f} ms"

        dashboard = f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⏱️  INTERVIEW TURN #{self.turn_number} LATENCY BREAKDOWN (Stage: {self.stage})
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Speculative Fast LLM (TTFT): {fast_ttft_str:<12} (Sarvam {settings.FAST_LLM_MODEL})
│ 2. Deep Reasoning Main LLM (TTFT): {main_ttft_str:<10} ({settings.MAIN_LLM_MODEL.split('/')[-1]})
│ 3. 🎯 E2E Response Latency:      {e2e_str:<10} [User Speech End ➔ Audio Playback]
│ 4. Total Turn Duration (w/ Audio): {total_dur_str:<10} (Sarvam {settings.SARVAM_TTS_MODEL})
└─────────────────────────────────────────────────────────────────────────────┘"""
        print(dashboard)

    def _push_to_opik(self):
        opik_client = get_opik_client()
        if not opik_client:
            return

        try:
            trace = opik_client.trace(
                name=f"turn_{self.turn_number}_{self.stage}",
                input={"user_text": self.user_text, "stage": self.stage},
                output={"assistant_text": self.response_text},
                tags=[self.stage, self.interview_type, self.candidate_name],
                metadata={
                    "room_id": self.room_id,
                    "user_id": self.user_id,
                    "candidate_name": self.candidate_name,
                    "interview_type": self.interview_type,
                    "stage": self.stage,
                    "turn_number": self.turn_number,
                    "e2e_response_latency_ms": self.e2e_response_latency_ms,
                    "fast_llm_ttft_ms": self.fast_llm_ttft_ms,
                    "main_llm_ttft_ms": self.main_llm_ttft_ms,
                    "total_turn_duration_ms": self.total_turn_duration_ms,
                }
            )

            # Fast LLM Span
            if self.fast_llm_total_ms is not None:
                fast_span = trace.span(
                    name="fast_llm_speculative",
                    type="llm",
                    input={"prompt": "Fast Bridge Speculation"},
                    output={"output": self.fast_llm_output},
                    metadata={
                        "model": settings.FAST_LLM_MODEL,
                        "ttft_ms": self.fast_llm_ttft_ms,
                        "latency_ms": self.fast_llm_total_ms,
                    }
                )
                fast_span.end()

            # Main LLM Span
            if self.main_llm_total_ms is not None:
                main_span = trace.span(
                    name="main_llm_reasoning",
                    type="llm",
                    input={"user_text": self.user_text, "stage": self.stage},
                    output={"response": self.main_llm_output or self.response_text},
                    metadata={
                        "model": settings.MAIN_LLM_MODEL,
                        "ttft_ms": self.main_llm_ttft_ms,
                        "latency_ms": self.main_llm_total_ms,
                    }
                )
                main_span.end()

            # State Evaluator Span
            if self.eval_latency_ms is not None:
                eval_span = trace.span(
                    name="state_evaluator",
                    type="llm",
                    input={"stage": self.stage},
                    output={
                        "reasoning": self.eval_reasoning,
                        "score": self.eval_score,
                        "objective_met": self.eval_objective_met,
                    },
                    metadata={"latency_ms": self.eval_latency_ms}
                )
                eval_span.end()

            trace.end()
        except Exception as e:
            logger.debug(f"Opik logging error (non-fatal): {e}")
