"""
Environment variables, per-engine model defaults, and tunable limits.
Nothing here has side effects beyond reading the environment.
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID   = int(os.getenv("TELEGRAM_API_ID"))   # from my.telegram.org
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")      # from my.telegram.org

# API keys — only the one you use needs to be filled
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")    # from openrouter.ai/keys
GROQ_API_KEY        = os.getenv("GROQ_API_KEY")          # from console.groq.com
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")  # from console.anthropic.com

# Model defaults per engine (change if you prefer a different model)
ENGINE_MODELS = {
    "openrouter": "openai/gpt-5.6-luna",     # smartest, reasoning enabled
    "groq":       "llama-3.3-70b-versatile",  # fast & free
    "claude":     "claude-haiku-4-5-20251001",  # fast & cheap
    "ollama":     "mistral",                  # local model name
}

OLLAMA_BASE_URL     = "http://localhost:11434"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Reasoning models spend part of the token budget thinking before they answer,
# so the cap has to cover reasoning + summary, not just the summary.
OPENROUTER_MAX_TOKENS = 8192

# Telegram rejects any single message over 4096 characters. Leave headroom for part markers.
TELEGRAM_MAX_CHARS = 4000

# Telethon session file (reused across runs after the first login).
SESSION_NAME = "tg_session"
