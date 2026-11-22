"""Client LLM compatible OpenAI : fonctionne avec Ollama, Groq, OpenRouter, Gemini..."""
import os
from openai import OpenAI

_client = None


def chat(messages, temperature=0.2):
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.getenv("LLM_API_KEY", "ollama"),
        )
    r = _client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "llama3.2"),
        messages=messages,
        temperature=temperature,
    )
    return r.choices[0].message.content or ""
