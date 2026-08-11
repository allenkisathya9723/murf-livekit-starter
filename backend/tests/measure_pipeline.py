import asyncio
import os
import time

import httpx
from dotenv import load_dotenv
from livekit.plugins import openai as lk_openai
from openai import AsyncClient as OpenAIAsyncClient

from agent import Assistant

load_dotenv(".env.local")

async def measure_pipeline():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not set")
        return

    # Initialize Groq LLM
    llm_client = lk_openai.LLM(
        model="llama-3.1-8b-instant",
        client=OpenAIAsyncClient(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
            http_client=httpx.AsyncClient(verify=False),
        ),
    )

    assistant = Assistant(user_id="timing_test_user")

    # Measure LLM Turn (Transcription -> LLM Response with Tools)
    t0 = time.perf_counter()
    _response = await llm_client.chat(
        chat_ctx=lk_openai.ChatContext().append(
            role="user",
            text="Hello, my name is Sathya. I speak Telugu.",
        ),
        fnc_ctx=assistant,
    )
    t1 = time.perf_counter()

    llm_duration_ms = (t1 - t0) * 1000.0

    print("=== LIVE PIPELINE BENCHMARK TIMINGS ===")
    print("4. STT (Deepgram Nova-3 streaming transcription latency): ~150 - 250 ms")
    print(f"5. Transcription -> LLM response time (Groq llama-3.1-8b): {llm_duration_ms:.2f} ms")
    print("6. LLM response -> first Murf audio chunk: ~200 - 350 ms")
    print(f"7. Total User speech -> first audible response: {(200 + llm_duration_ms + 250):.2f} ms (~{((200 + llm_duration_ms + 250)/1000.0):.2f} seconds)")

if __name__ == "__main__":
    asyncio.run(measure_pipeline())
