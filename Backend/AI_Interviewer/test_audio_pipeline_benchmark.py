import asyncio
import aiohttp
import base64
import io
import json
import os
import time
import wave
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI, RealtimeAudioInput, RealtimeEnd

load_dotenv(".env.local")
load_dotenv(".env")

API_KEY = os.getenv("SARVAM_API_KEY", "").strip()

# ==============================================================================
# 1. TTS BENCHMARK (WebSocket Streaming & REST)
# ==============================================================================
async def test_tts_streaming(text: str = "Hi Vishal, welcome to ThinkAloudAI. Let's start the interview.") -> Dict[str, Any]:
    print("\n" + "="*70)
    print("🔊 [1] BENCHMARKING TTS: Sarvam WebSocket Streaming (bulbul:v3)")
    print("="*70)
    print(f"📝 Input Text : \"{text}\"")

    if not API_KEY or API_KEY.startswith("your_"):
        print("❌ SKIPPED: Invalid SARVAM_API_KEY")
        return {"status": "SKIPPED"}

    from livekit.plugins import sarvam
    async with aiohttp.ClientSession() as session:
        t_start = time.time()
        t_first_byte: Optional[float] = None
        total_audio_bytes = 0
        chunks_count = 0

        try:
            tts_plugin = sarvam.TTS(
                api_key=API_KEY,
                model="bulbul:v3",
                speaker="shubh",
                target_language_code="en-IN",
                speech_sample_rate=22050,
                pace=1.0,
                ws_url="wss://api.sarvam.ai/text-to-speech/ws",
                send_completion_event=True,
                http_session=session,
            )

            stream = tts_plugin.stream()
            stream.push_text(text)
            stream.flush()
            stream.end_input()

            print("   Streaming audio frames from WebSocket... ", end="", flush=True)
            async for event in stream:
                if hasattr(event, "frame") and event.frame:
                    if t_first_byte is None:
                        t_first_byte = time.time()
                    frame_bytes = len(event.frame.data.tobytes())
                    total_audio_bytes += frame_bytes
                    chunks_count += 1
                    print("🎵", end="", flush=True)

            t_end = time.time()
            print() # newline

            ttfb_ms = ((t_first_byte or t_end) - t_start) * 1000
            total_duration_ms = (t_end - t_start) * 1000
            audio_duration_sec = total_audio_bytes / (22050 * 2) if total_audio_bytes > 0 else 0
            rtf = (total_duration_ms / 1000.0) / audio_duration_sec if audio_duration_sec > 0 else 0

            print(f"   ⚡ Time To First Audio Byte (TTFAB) : {ttfb_ms:.1f} ms")
            print(f"   ⏱️ Total Audio Synthesis Time       : {total_duration_ms:.1f} ms")
            print(f"   📦 Audio Packets Received           : {chunks_count} frames ({total_audio_bytes:,} bytes)")
            print(f"   🕒 Generated Audio Duration         : {audio_duration_sec:.2f} seconds")
            print(f"   🚀 Real-Time Factor (RTF)           : {rtf:.3f}x (lower is faster)")
            print(f"   ✅ WebSocket TTS Status             : PASSED")
            return {
                "status": "PASSED",
                "ttfb_ms": ttfb_ms,
                "total_ms": total_duration_ms,
                "audio_sec": audio_duration_sec,
                "audio_bytes": total_audio_bytes,
            }
        except Exception as e:
            print(f"\n   ❌ WebSocket TTS Failed: {e}")
            return {"status": "FAILED", "error": str(e)}

# ==============================================================================
# 2. STT BENCHMARK (Real-Time WebSocket Streaming)
# ==============================================================================
async def test_stt_realtime() -> Dict[str, Any]:
    print("\n" + "="*70)
    print("🎙️ [2] BENCHMARKING STT: Sarvam Saaras v3 Realtime WebSocket")
    print("="*70)

    if not API_KEY or API_KEY.startswith("your_"):
        print("❌ SKIPPED: Invalid SARVAM_API_KEY")
        return {"status": "SKIPPED"}

    client = AsyncSarvamAI(api_subscription_key=API_KEY)
    ground_truth_text = "I am ready for the technical interview session today."
    print(f"   Generating reference spoken speech: \"{ground_truth_text}\"...")
    
    tts_res = await client.text_to_speech.convert(
        text=ground_truth_text,
        language_code="en-IN",
        speaker="shubh",
        model="bulbul:v3",
        speech_sample_rate=16000,
        output_audio_codec="wav",
    )
    speech_wav_bytes = base64.b64decode(tts_res.audios[0])
    pcm_payload = speech_wav_bytes[44:] if speech_wav_bytes.startswith(b"RIFF") else speech_wav_bytes
    print(f"   ✅ Reference speech audio synthesized ({len(speech_wav_bytes):,} bytes)")

    t_connect_start = time.time()
    t_connected: Optional[float] = None
    t_first_transcript: Optional[float] = None
    final_transcript = ""

    try:
        async with client.speech_to_text_realtime_streaming.connect(
            language_code="en-IN",
            model="saaras:v3-realtime",
            mode="transcribe",
            stream_type="balanced",
            sample_rate="16000",
            encoding="linear16",
        ) as ws:
            t_connected = time.time()
            handshake_ms = (t_connected - t_connect_start) * 1000
            print(f"   ⚡ WebSocket Handshake Connected in {handshake_ms:.1f} ms")

            # Stream audio in 100ms chunks (3200 bytes)
            async def send_stream():
                chunk_size = 3200
                offset = 0
                while offset < len(pcm_payload):
                    chunk = pcm_payload[offset : offset + chunk_size]
                    offset += chunk_size
                    b64_chunk = base64.b64encode(chunk).decode("utf-8")
                    await ws.send_realtime_audio_input(RealtimeAudioInput(audio=b64_chunk))
                    await asyncio.sleep(0.08) # stream at near real-time cadence
                await ws.send_realtime_end(RealtimeEnd())

            async def receive_transcripts():
                nonlocal t_first_transcript, final_transcript
                async for message in ws:
                    event = getattr(message, "event", None)
                    text = getattr(message, "text", "")
                    if event == "transcript.partial":
                        if t_first_transcript is None:
                            t_first_transcript = time.time()
                        print(f"   [Partial] \"{text}\"")
                    elif event == "transcript.final":
                        final_transcript = text
                        print(f"   [Final]   \"{text}\"")
                        return
                    elif event in ("session.end", "speech.end"):
                        return
                    elif event == "error":
                        print(f"   ❌ STT Error Event: {message}")
                        return

            await asyncio.gather(send_stream(), receive_transcripts())

        t_end = time.time()
        ttft_stt_ms = ((t_first_transcript or t_end) - t_connected) * 1000 if t_connected else 0
        total_stt_ms = (t_end - t_connect_start) * 1000

        print(f"\n   ⚡ STT Handshake Latency        : {handshake_ms:.1f} ms")
        print(f"   ⚡ Time To First Transcript    : {ttft_stt_ms:.1f} ms")
        print(f"   ⏱️ Total STT Processing Time    : {total_stt_ms:.1f} ms")
        print(f"   📝 Recognized Transcript       : \"{final_transcript.strip()}\"")
        print(f"   ✅ Real-time STT Status        : PASSED")
        return {
            "status": "PASSED",
            "handshake_ms": handshake_ms,
            "ttft_ms": ttft_stt_ms,
            "total_ms": total_stt_ms,
            "transcript": final_transcript,
        }
    except Exception as e:
        print(f"   ❌ Real-time STT Failed: {e}")
        return {"status": "FAILED", "error": str(e)}

# ==============================================================================
# 3. END-TO-END ROUND TRIP (STT -> LLM -> TTS)
# ==============================================================================
async def test_end_to_end_pipeline():
    print("\n" + "#"*70)
    print("#   🚀 [3] END-TO-END VOICE LOOP BENCHMARK: STT -> LLM -> TTS   #")
    print("#"*70)

    from openai import AsyncOpenAI
    import httpx

    t0_loop = time.time()
    candidate_speech = "I have solved Two Sum using a hash map in O(N) time."
    print(f"1️⃣ Candidate Speaks : \"{candidate_speech}\"")

    # Step 1: Synthesize voice to feed to STT
    client = AsyncSarvamAI(api_subscription_key=API_KEY)
    tts_res = await client.text_to_speech.convert(
        text=candidate_speech,
        language_code="en-IN",
        speaker="shubh",
        model="bulbul:v3",
        speech_sample_rate=16000,
        output_audio_codec="wav",
    )
    wav_bytes = base64.b64decode(tts_res.audios[0])
    pcm = wav_bytes[44:]

    # Step 2: Stream to STT
    t_stt_start = time.time()
    transcript = ""
    async with client.speech_to_text_realtime_streaming.connect(
        language_code="en-IN",
        model="saaras:v3-realtime",
        mode="transcribe",
        stream_type="balanced",
        sample_rate="16000",
        encoding="linear16",
    ) as ws:
        async def send_pcm():
            chunk_sz = 3200
            for i in range(0, len(pcm), chunk_sz):
                c = pcm[i:i+chunk_sz]
                await ws.send_realtime_audio_input(RealtimeAudioInput(audio=base64.b64encode(c).decode("utf-8")))
                await asyncio.sleep(0.04)
            await ws.send_realtime_end(RealtimeEnd())

        async def get_tx():
            nonlocal transcript
            async for m in ws:
                if getattr(m, "event", None) == "transcript.final":
                    transcript = getattr(m, "text", "")
                    return
                elif getattr(m, "event", None) == "session.end":
                    return

        await asyncio.gather(send_pcm(), get_tx())

    stt_latency_ms = (time.time() - t_stt_start) * 1000
    print(f"2️⃣ STT Recognized  : \"{transcript.strip()}\" ({stt_latency_ms:.1f}ms)")

    # Step 3: Stream to LLM (gemma4)
    t_llm_start = time.time()
    llm_client = AsyncOpenAI(
        api_key=API_KEY,
        base_url="https://api.sarvam.ai/v2",
        http_client=httpx.AsyncClient(timeout=10.0)
    )
    stream = await llm_client.chat.completions.create(
        model="gemma4",
        messages=[
            {"role": "system", "content": "You are Aarav, a technical interviewer. Respond in 1 brief sentence acknowledging the candidate's answer."},
            {"role": "user", "content": transcript or candidate_speech}
        ],
        max_tokens=60,
        stream=True,
    )
    llm_tokens = []
    t_llm_first_token = None
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                if t_llm_first_token is None:
                    t_llm_first_token = time.time()
                llm_tokens.append(delta)

    llm_response = "".join(llm_tokens).strip()
    llm_ttft_ms = ((t_llm_first_token or time.time()) - t_llm_start) * 1000
    llm_total_ms = (time.time() - t_llm_start) * 1000
    print(f"3️⃣ LLM Answered    : \"{llm_response}\" (TTFT: {llm_ttft_ms:.1f}ms, Total: {llm_total_ms:.1f}ms)")

    # Step 4: Stream LLM Output to TTS
    t_tts_start = time.time()
    from livekit.plugins import sarvam
    async with aiohttp.ClientSession() as session:
        tts_plugin = sarvam.TTS(
            api_key=API_KEY,
            model="bulbul:v3",
            speaker="shubh",
            target_language_code="en-IN",
            speech_sample_rate=22050,
            ws_url="wss://api.sarvam.ai/text-to-speech/ws",
            http_session=session,
        )
        tts_stream = tts_plugin.stream()
        tts_stream.push_text(llm_response)
        tts_stream.flush()
        tts_stream.end_input()
        tts_first_byte = None
        async for ev in tts_stream:
            if hasattr(ev, "frame") and ev.frame:
                if tts_first_byte is None:
                    tts_first_byte = time.time()

    tts_ttfb_ms = ((tts_first_byte or time.time()) - t_tts_start) * 1000
    tts_total_ms = (time.time() - t_tts_start) * 1000
    print(f"4️⃣ TTS Audio Out   : Synthesized (TTFAB: {tts_ttfb_ms:.1f}ms, Total: {tts_total_ms:.1f}ms)")

    print("\n" + "="*70)
    print("📊 COMPLETE CONVERSATIONAL TURN LATENCY BREAKDOWN")
    print("="*70)
    print(f"  • STT Transcription Latency : {stt_latency_ms:.1f} ms")
    print(f"  • LLM Time-To-First-Token   : {llm_ttft_ms:.1f} ms")
    print(f"  • TTS Time-To-First-Audio   : {tts_ttfb_ms:.1f} ms")
    print(f"  ──────────────────────────────────────────────────")
    print(f"  ⚡ Perceived Turn Response  : {stt_latency_ms + llm_ttft_ms + tts_ttfb_ms:.1f} ms")
    print("="*70 + "\n")

async def main():
    print("\n" + "#"*70)
    print("#        ThinkAloudAI - Comprehensive Audio (TTS & STT) Benchmark     #")
    print("#"*70)

    # 1. Test TTS
    await test_tts_streaming("Hi Vishal, welcome to ThinkAloudAI. Let's start the interview.")

    # 2. Test STT
    await test_stt_realtime()

    # 3. Test End-to-End Loop
    await test_end_to_end_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
