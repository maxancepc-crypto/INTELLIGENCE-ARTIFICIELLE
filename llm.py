"""Client LLM compatible OpenAI : Ollama, Groq, OpenRouter, Gemini..."""

import os
import sys
from openai import OpenAI

_client = None


def chat(messages, temperature=0.2):
    global _client
    base = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("LLM_MODEL", "llama3.2")
    if _client is None:
        _client = OpenAI(
            base_url=base,
            api_key=os.getenv("LLM_API_KEY", "ollama"),
            timeout=60,
            max_retries=1,
        )
    try:
        r = _client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return r.choices[0].message.content or ""
    except Exception as e:
        print(f"[LLM ERROR] base={base} model={model} -> {type(e).__name__}: {e}",
              file=sys.stderr, flush=True)
        raise
