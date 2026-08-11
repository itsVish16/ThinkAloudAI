# Integrate Sarvam AI for TTS and LLM

We will replace the current Fireworks/OpenAI LLM and Speechmatics/OpenAI TTS implementations in the `AI_Interviewer` service with Sarvam AI's models to achieve ultra-low latency.

> [!IMPORTANT]
> **User Review Required**
> 
> You will need to provide a valid `SARVAM_API_KEY` in your `.env` and `.env.local` files once this is deployed. Please confirm if you have your Sarvam API credentials ready.

## Open Questions

> [!WARNING]
> 1. You specifically mentioned **TTS and LLM**. Would you also like to switch the **STT (Speech-to-Text)** engine to Sarvam AI (`saaras:v3`) for Indian accent optimizations, or keep the existing Speechmatics / OpenAI fallback for STT? 
> 2. For TTS, Sarvam uses `bulbul:v3` with various speakers. Is there a specific voice/speaker you prefer (e.g., `"shubh"`, `"amartya"`, `"meera"`), and should the default accent target `"en-IN"` (Indian English)?

## Proposed Changes

---

### Dependencies

#### [MODIFY] [pyproject.toml](file:///Users/vishal/Desktop/ThinkAloudAI/Backend/AI_Interviewer/pyproject.toml)
- Add `livekit-plugins-sarvam` to the `dependencies` block to install the official LiveKit integration for Sarvam.

### Configuration

#### [MODIFY] [config.py](file:///Users/vishal/Desktop/ThinkAloudAI/Backend/AI_Interviewer/app/config.py)
- Add `SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")`.
- Change default `LLM_BASE_URL` to `https://api.sarvam.ai/v1`.
- Change default `LLM_MODEL` to `sarvam-105b` (or similar depending on preference).

#### [MODIFY] [.env.example](file:///Users/vishal/Desktop/ThinkAloudAI/Backend/AI_Interviewer/.env.example)
- Add `SARVAM_API_KEY=your_sarvam_api_key_here`.
- Update `LLM_BASE_URL` and `LLM_MODEL` examples.

### Core Application Logic

#### [MODIFY] [worker.py](file:///Users/vishal/Desktop/ThinkAloudAI/Backend/AI_Interviewer/app/worker.py)
- Import the Sarvam LiveKit plugin: `from livekit.plugins import sarvam`.
- Replace the TTS initialization (`speechmatics.TTS()` / `openai.TTS()`) with:
  ```python
  tts = sarvam.TTS(
      model="bulbul:v3", 
      speaker="shubh", 
      target_language_code="en-IN"
  )
  ```
- Make sure `SARVAM_API_KEY` is validated on startup or passed directly to the plugin if required.

## Verification Plan

### Automated Tests
- We will run `uv sync` to ensure dependencies resolve correctly.

### Manual Verification
- Start the `AI_Interviewer` worker locally (`python -m app.worker start`) with your new `SARVAM_API_KEY` and verify it connects to LiveKit Cloud without plugin initialization errors.
- Connect to an interview room via the frontend and verify that the AI responds quickly and speaks using the Sarvam voice.
