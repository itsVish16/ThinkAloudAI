import asyncio
import os
import time
from typing import Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI
import httpx

load_dotenv(".env.local")
load_dotenv(".env")

__test__ = False

async def test_llm_model(
    provider_name: str,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str = "Hi, I am Vishal. I am ready for the technical interview. Please acknowledge in two brief sentences.",
    max_tokens: int = 100,
):
    print(f"\n{'='*70}")
    print(f"🔬 Provider : {provider_name}")
    print(f"🌐 Endpoint : {base_url}")
    print(f"🤖 Model    : {model}")
    print(f"🔑 Key      : {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    print(f"{'='*70}")

    if not api_key or api_key.startswith("your_") or api_key == "dummy_key":
        print(f"❌ SKIPPED: Invalid or missing API Key")
        return {"status": "SKIPPED", "ttft_ms": None, "total_ms": None, "tokens_per_sec": None}

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=httpx.AsyncClient(timeout=10.0)
    )
    messages = [
        {"role": "system", "content": "You are Aarav, an expert AI Technical Interviewer from ThinkAloudAI. Be conversational, natural, and concise."},
        {"role": "user", "content": prompt}
    ]

    # 1. Non-Streaming Test
    print("\n[1] Non-Streaming Completion Test:")
    t0 = time.time()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            stream=False,
        )
        non_stream_latency = (time.time() - t0) * 1000
        content = resp.choices[0].message.content or ""
        print(f"    Latency : {non_stream_latency:.1f} ms")
        print(f"    Output  : \"{content.strip()}\"")
    except Exception as e:
        print(f"    ❌ Non-streaming Failed: {e}")

    # 2. Streaming Test (LiveKit Voice Agent Turn Pipeline)
    print("\n[2] Real-time Streaming Test (LiveKit Flow):")
    start_time = time.time()
    first_token_time: Optional[float] = None
    chunks_count = 0
    full_text = []

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            stream=True,
        )
        
        print("    Stream  : \"", end="", flush=True)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta_content = chunk.choices[0].delta.content or ""
                if delta_content:
                    if first_token_time is None:
                        first_token_time = time.time()
                    chunks_count += 1
                    full_text.append(delta_content)
                    print(delta_content, end="", flush=True)

        end_time = time.time()
        print("\"")
        
        total_time_ms = (end_time - start_time) * 1000
        ttft_ms = ((first_token_time or end_time) - start_time) * 1000
        streamed_text = "".join(full_text).strip()
        est_tokens = len(streamed_text) / 4.0
        generation_time_sec = (end_time - (first_token_time or start_time))
        tok_per_sec = (est_tokens / generation_time_sec) if generation_time_sec > 0 else 0

        print(f"    ⚡ TTFT (Time-To-First-Token) : {ttft_ms:.1f} ms")
        print(f"    ⏱️ Total Streaming Latency     : {total_time_ms:.1f} ms")
        print(f"    📦 Streaming Chunks Received   : {chunks_count}")
        print(f"    🚀 Generation Throughput       : {tok_per_sec:.1f} tokens/sec")
        print(f"    ✅ Status                      : PASSED")
        return {"status": "PASSED", "ttft_ms": ttft_ms, "total_ms": total_time_ms, "tokens_per_sec": tok_per_sec}
    except Exception as e:
        print(f"\"\n    ❌ Streaming Failed: {e}")
        return {"status": "FAILED", "ttft_ms": None, "total_ms": None, "tokens_per_sec": None}

async def main():
    sarvam_key = os.getenv("SARVAM_API_KEY", "").strip()
    fireworks_key = (os.getenv("FIREWORKS_API_KEY") or os.getenv("ANALYSIS_LLM_API_KEY", "")).strip()

    print("\n" + "#"*70)
    print("#       ThinkAloudAI - Comprehensive LLM Latency & Health Check       #")
    print("#"*70)

    results = {}

    # Test 1: Sarvam gemma4 on /v2 (Active Voice Agent Model)
    if sarvam_key:
        results["Sarvam gemma4 (/v2)"] = await test_llm_model(
            provider_name="Sarvam AI (Conversational Voice Agent)",
            base_url="https://api.sarvam.ai/v2",
            api_key=sarvam_key,
            model="gemma4",
        )

    # Test 2: Fireworks GLM-5.2 Fast (Analysis / Backup Model)
    if fireworks_key:
        results["Fireworks glm-5p2-fast"] = await test_llm_model(
            provider_name="Fireworks AI (Analysis / Mentorship)",
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=fireworks_key,
            model="accounts/fireworks/routers/glm-5p2-fast",
        )

    print("\n" + "="*70)
    print(f"{'LLM Model / Provider':<30} | {'Status':<10} | {'TTFT (ms)':<10} | {'Total (ms)':<10} | {'Tokens/s':<10}")
    print("-" * 70)
    for model_name, data in results.items():
        st = data["status"]
        ttft = f"{data['ttft_ms']:.1f}" if data['ttft_ms'] else "N/A"
        tot = f"{data['total_ms']:.1f}" if data['total_ms'] else "N/A"
        tps = f"{data['tokens_per_sec']:.1f}" if data['tokens_per_sec'] else "N/A"
        print(f"{model_name:<30} | {st:<10} | {ttft:<10} | {tot:<10} | {tps:<10}")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
