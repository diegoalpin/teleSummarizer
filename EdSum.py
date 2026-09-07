"""
Telegram Group Summarizer
=========================
Summarizes Telegram group messages using a switchable AI engine.

Supported engines:
  - openrouter : OpenRouter (default, openai/gpt-5.6-luna with reasoning)
  - groq       : Groq API (fast, free tier)
  - claude     : Anthropic Claude API
  - ollama     : Local Ollama (fully offline)

Usage:
  python EdSum.py --mode count  --value 200                      # openrouter (default)
  python EdSum.py --mode hours  --value 6    --engine claude
  python EdSum.py --mode since  --value "2024-01-15 09:00"  --engine ollama

Setup:
  pip install telethon groq anthropic requests python-dotenv
"""

import asyncio
import argparse
import os
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from typing import List
from dotenv import load_dotenv
from slang_glossary import format_slang_for_prompt

# ─────────────────────────────────────────────
# CONFIG — fill these in before running
# ─────────────────────────────────────────────
load_dotenv()

TELEGRAM_API_ID   = int(os.getenv("TELEGRAM_API_ID"))           # from my.telegram.org
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")          # from my.telegram.org
GROUP_NAME        = "Social Trade Exclusive"          # e.g. "My Dev Group" or "mygroupusername"

# API keys — only the one you use needs to be filled
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")   # from openrouter.ai/keys
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")          # from console.groq.com
ANTHROPIC_API_KEY = ""          # from console.anthropic.com

# Model defaults per engine (change if you prefer a different model)
ENGINE_MODELS = {
    "openrouter": "openai/gpt-5.6-luna",     # smartest, reasoning enabled
    "groq"   : "llama-3.3-70b-versatile",       # fast & free
    "claude" : "claude-haiku-4-5-20251001",  # fast & cheap
    "ollama" : "mistral",              # local model name
}

OLLAMA_BASE_URL     = "http://localhost:11434"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Reasoning models spend part of the token budget thinking before they answer,
# so the cap has to cover reasoning + summary, not just the summary.
OPENROUTER_MAX_TOKENS = 8192

# Telegram rejects any single message over 4096 characters. Leave headroom for part markers.
TELEGRAM_MAX_CHARS = 4000

# ─────────────────────────────────────────────
# SUMMARIZATION ENGINES
# ─────────────────────────────────────────────
    
def build_prompt(messages: List[str], label: str) -> str:
    combined = "\n".join(messages)
    slang_block = format_slang_for_prompt()
    return (
        f"You are summarizing a Telegram group chat ({label}) focused on Indonesian stock market discussion.\n"
        "Your goal is to extract investment ideas, stock analysis, and notable insights — not to narrate who said what.\n\n"

        "LANGUAGE & SLANG:\n"
        "The chat is written in informal Bahasa Indonesia (colloquial/slang), mixed occasionally with English financial terms.\n"
        "Do NOT translate the summary into Bahasa — always summarize in English.\n"
        "Be aware of common Indonesian stock market slang, including but not limited to:\n"
        f"{slang_block}\n"
        "Tickers may appear in lowercase mid-sentence — always normalize them to uppercase.\n"
        "Indonesian tickers are 4-letter uppercase codes, e.g. 'BBRI', 'BBCA', 'TLKM'. Detect them carefully.\n\n"

        "SPECIAL INSTRUCTION — Key Contributor (ID: 1200423176):\n"
        "This user's messages carry higher weight. If they mention a ticker, share an analysis, or express a view,\n"
        "always highlight it explicitly with a ⭐ marker. Do not skip or merge their points into group discussion.\n\n"

        "SUMMARIZATION RULES:\n"
        "- Organize the summary by STOCK TICKER, not by person or chronology.\n"
        "- For each ticker: summarize the thesis, sentiment (bullish/bearish/neutral), key arguments, and any price levels or catalysts mentioned.\n"
        "- If no ticker is tied to a topic (e.g. macro discussion, strategy), group it under '🌐 MACRO & GENERAL'.\n"
        "- Attribution is secondary — only name someone if their view is notably distinct or if it's the key contributor.\n"
        "- If the key contributor (ID: 1200423176) speaks on a ticker, always surface their view separately under that ticker.\n\n"

        "Structure your summary as follows:\n\n"

        "📈 [TICKER]\n"
        "  Sentiment: Bullish / Bearish / Mixed\n"
        "  Key idea: One-line thesis summary.\n"
        "  Discussion: 2–4 sentences summarizing the arguments, data points, or price levels discussed.\n"
        "  ⭐ Key contributor's view: [Only include if ID 1200423176 commented. Closely paraphrase their point.]\n\n"

        "(Repeat the above block for each ticker discussed)\n\n"

        "🌐 MACRO & GENERAL\n"
        "  Summarize any non-ticker topics: market sentiment, sector rotation, economic news, strategy, etc.\n"
        "  ⭐ Key contributor's view: [If applicable]\n\n"

        "🔗 LINKS & MEDIA\n"
        "  • List any links or media shared and what they relate to. Skip if none.\n\n"

        "⚠️ OPEN IDEAS & FOLLOW-UPS\n"
        "  • Any unresolved questions, upcoming catalysts to watch, or stocks flagged for future discussion.\n\n"

        f"Messages:\n{combined}\n\n"
        "Summary:"
    )

# Example output you can expect
# 📌 TOPICS
# - Alice raised concerns about the deployment timeline; Bob agreed it needs revisiting.
# - The group discussed which framework to use for the frontend.
# - Carol asked if the staging environment is ready; no answer yet.

# 🔗 LINKS & MEDIA
# - Dave shared a link to the new Figma mockups.

# ⚠️ FOLLOW-UPS
# - Carol's question about staging is unresolved — needs someone to follow up.
# - Alice and Bob to sync on the deployment date.
# Just drop the function as a replacement in your existing script — no other changes needed.


def summarize_openrouter(prompt: str, model: str) -> str:
    import requests
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set — add it to your .env")

    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "reasoning": {"enabled": True},
            "max_tokens": OPENROUTER_MAX_TOKENS,
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
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def summarize_claude(prompt: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def summarize_ollama(prompt: str, model: str) -> str:
    import requests
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["response"]


def summarize(messages: List[str], label: str, engine: str) -> str:
    model  = ENGINE_MODELS[engine]
    prompt = build_prompt(messages, label)

    print(f"  Engine  : {engine} ({model})")

    if engine == "openrouter":
        return summarize_openrouter(prompt, model)
    elif engine == "groq":
        return summarize_groq(prompt, model)
    elif engine == "claude":
        return summarize_claude(prompt, model)
    elif engine == "ollama":
        return summarize_ollama(prompt, model)
    else:
        raise ValueError(f"Unknown engine: {engine}")


# ─────────────────────────────────────────────
# TELEGRAM HELPERS
# ─────────────────────────────────────────────

def tg_len(text: str) -> int:
    """Telegram measures message length in UTF-16 code units, so emoji count as 2."""
    return len(text.encode("utf-16-le")) // 2


def split_for_telegram(text: str, limit: int = TELEGRAM_MAX_CHARS) -> List[str]:
    """Break a long summary into Telegram-sized chunks, splitting on line boundaries."""
    chunks: List[str] = []
    current = ""

    for line in text.split("\n"):
        # A single line over the limit can only be split mid-line.
        while tg_len(line) > limit:
            if current:
                chunks.append(current.rstrip("\n"))
                current = ""
            head = line[:limit]
            while tg_len(head) > limit:
                head = head[:-1]
            chunks.append(head)
            line = line[len(head):]

        if current and tg_len(current) + tg_len(line) + 1 > limit:
            chunks.append(current.rstrip("\n"))
            current = ""
        current += line + "\n"

    if current.strip():
        chunks.append(current.rstrip("\n"))
    return chunks or [text]


async def find_group(client, name: str):
    async for dialog in client.iter_dialogs():
        if name.lower() in dialog.name.lower():
            return dialog
    return None


async def fetch_by_count(client, entity, count: int) -> List[str]:
    messages = []
    async for msg in client.iter_messages(entity, limit=count):
        if msg.text:
            try:
                sender = (await msg.get_sender()).first_name or "Unknown"
            except Exception:
                sender = "Unknown"
            messages.append(f"{sender}: {msg.text}")
    messages.reverse()
    return messages


async def fetch_by_time(client, entity, since: datetime) -> List[str]:
    messages = []
    async for msg in client.iter_messages(entity, offset_date=since, reverse=True):
        if msg.text:
            try:
                sender = (await msg.get_sender()).first_name or "Unknown"
            except Exception:
                sender = "Unknown"
            messages.append(f"{sender}: {msg.text}")
    return messages


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

async def run(mode: str, value: str, engine: str):
    tg = TelegramClient("tg_session", TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await tg.start()

    print(f"\n📡 Finding group: {GROUP_NAME}")
    target = await find_group(tg, GROUP_NAME)
    if not target:
        print("❌ Group not found. Check GROUP_NAME in config.")
        return

    print(f"✅ Found: {target.name}")

    # ── Fetch messages ──────────────────────────
    if mode == "count":
        count = int(value)
        print(f"\n📥 Fetching last {count} messages...")
        messages = await fetch_by_count(tg, target.entity, count)
        label = f"last {count} messages"

    elif mode == "hours":
        hours = float(value)
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        print(f"\n📥 Fetching messages from the last {hours} hour(s)...")
        messages = await fetch_by_time(tg, target.entity, since)
        label = f"last {hours} hour(s)"

    elif mode == "since":
        since_dt = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        print(f"\n📥 Fetching messages since {value} UTC...")
        messages = await fetch_by_time(tg, target.entity, since_dt)
        label = f"since {value} UTC"

    else:
        print(f"❌ Unknown mode: {mode}")
        return

    if not messages:
        print("⚠️  No messages found for the given range.")
        return

    print(f"💬 {len(messages)} messages fetched.")

    # ── Summarize ───────────────────────────────
    print(f"\n🤖 Summarizing...")
    summary = summarize(messages, label, engine)

    # ── Send to Saved Messages ──────────────────
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = (
        f"📋 **Group Summary — {target.name}**\n"
        f"🕐 {now_str}  |  📝 {len(messages)} messages  |  ⚙️ {engine}\n\n"
        f"{summary}"
    )

    parts = split_for_telegram(full_message)
    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            part = f"{part}\n\n— part {i}/{len(parts)} —"
        await tg.send_message("me", part)

    suffix = f" in {len(parts)} messages" if len(parts) > 1 else ""
    print(f"\n✅ Summary sent to your Saved Messages{suffix}!")
    await tg.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telegram Group Summarizer")
    parser.add_argument(
        "--mode", choices=["count", "hours", "since"], required=True,
        help="How to select messages: by count, hours ago, or since a datetime"
    )
    parser.add_argument(
        "--value", required=True,
        help='Value for mode: number for count/hours, "YYYY-MM-DD HH:MM" for since'
    )
    parser.add_argument(
        "--engine", choices=["openrouter", "groq", "claude", "ollama"], default="openrouter",
        help="AI engine to use for summarization (default: openrouter)"
    )
    args = parser.parse_args()

    asyncio.run(run(args.mode, args.value, args.engine))