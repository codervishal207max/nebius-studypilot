import re

from openai import OpenAI

from . import config, settings

_client = None


def get_client():
    """OpenAI-compatible client pointed at Nebius Token Factory.
    The API key comes from NEBIUS_API_KEY in your .env file (see app/config.py)."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=config.NEBIUS_API_KEY or "missing-key",
            base_url=config.NEBIUS_BASE_URL,
        )
    return _client


def clean(text):
    """Reasoning models sometimes emit <think>...</think>; strip it."""
    if not text:
        return ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def chat(messages, tools=None, temperature=0.3, max_tokens=1200):
    kwargs = dict(
        model=settings.model(),  # the model name set in Settings (or LLM_MODEL from .env)
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return get_client().chat.completions.create(**kwargs).choices[0].message


def embed(texts):
    """Returns a list of embeddings, or None on failure (keyword search is the fallback)."""
    try:
        r = get_client().embeddings.create(model=config.EMBED_MODEL, input=texts)
        return [d.embedding for d in r.data]
    except Exception:
        return None
