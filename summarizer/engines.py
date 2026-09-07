"""
LLM backends. Each summarize_* function takes a fully-built prompt and a
model name, and returns the raw summary text.
"""
from . import config


def summarize_openrouter(prompt: str, model: str) -> str:
    import requests
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set — add it to your .env")

    response = requests.post(
        f"{config.OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "reasoning": {"enabled": True},
            "max_tokens": config.OPENROUTER_MAX_TOKENS,
        },
        timeout=300,
    )
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"OpenRouter error: {payload['error']}")

    content = payload["choices"][0]["message"].get("content")
    if not content:
        raise RuntimeError(
            "OpenRouter returned an empty summary — the model may have spent the whole "
            f"token budget reasoning (finish_reason: {payload['choices'][0].get('finish_reason')})"
        )
    return content


def summarize_groq(prompt: str, model: str) -> str:
    from groq import Groq
    client = Groq(api_key=config.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def summarize_claude(prompt: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def summarize_ollama(prompt: str, model: str) -> str:
    import requests
    response = requests.post(
        f"{config.OLLAMA_BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["response"]


_ENGINES = {
    "openrouter": summarize_openrouter,
    "groq": summarize_groq,
    "claude": summarize_claude,
    "ollama": summarize_ollama,
}


def summarize(prompt: str, engine: str) -> str:
    if engine not in _ENGINES:
        raise ValueError(f"Unknown engine: {engine}")
    model = config.ENGINE_MODELS[engine]
    print(f"  Engine  : {engine} ({model})")
    return _ENGINES[engine](prompt, model)
