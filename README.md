# teleSummarizer

Summarize Telegram group chats with a switchable LLM backend. Point it at a group, pick a time window, get a structured summary posted to your Saved Messages.

Ships with two scripts:
- **`TeleSummarizer.py`** — general-purpose, topic-organized with attribution
- **`EdSum.py`** — Indonesian stock market groups, ticker-first with sentiment and slang awareness

---

## How it works

```
Telegram Group → Telethon fetch → build_prompt() → LLM → Saved Messages
```

**Why Telethon (user client, not a bot):** bots can't read private groups. A user client can read any group you're a member of, which is the common case.

**Why four LLM engines:**
- `openrouter` (`openai/gpt-5.6-luna`, reasoning enabled) — **default.** Best summary quality; one key gets you any model OpenRouter hosts, so swapping models is a one-line change.
- `groq` (`llama-3.3-70b-versatile`) — free tier, very fast. Good fallback for high-frequency cron runs.
- `claude` (`claude-haiku-4-5`) — cheap and fast for dense or nuanced content.
- `ollama` (`mistral`, local) — fully offline; message content never leaves your machine.

**Why two scripts instead of one:** the prompt is the whole product. `TeleSummarizer.py` organizes by topic; `EdSum.py` reorganizes by stock ticker and bakes in an Indonesian slang glossary. Keeping them separate makes each one easy to hack.

---

## Installation

### 1. Clone and install dependencies

```bash
git clone https://github.com/diegoalpin/teleSummarizer.git
cd teleSummarizer
pip install telethon groq anthropic requests python-dotenv
```

### 2. Get Telegram API credentials

Go to [my.telegram.org](https://my.telegram.org), log in, and create an app to get your `api_id` and `api_hash`.

### 3. Create `.env`

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# LLM keys — only fill what you'll use
OPENROUTER_API_KEY=sk-or-v1-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
```

Get an OpenRouter key at [openrouter.ai/keys](https://openrouter.ai/keys) — it's the default engine.

### 4. Set your target group

Edit `GROUP_NAME` near the top of the script you're using:

```python
GROUP_NAME = "My Group Name"  # case-insensitive, partial match OK
```

### 5. Run

```bash
# Last 200 messages via OpenRouter / GPT-5.6 Luna (default engine)
python TeleSummarizer.py --mode count --value 200

# Last 6 hours via Groq
python TeleSummarizer.py --mode hours --value 6 --engine groq

# Since a specific datetime via local Ollama
python TeleSummarizer.py --mode since --value "2026-01-15 09:00" --engine ollama
```

On first run, Telethon will prompt for your phone number and a Telegram verification code. After that, `tg_session.session` is saved and reused automatically.

**CLI flags:**

| Flag | Required | Values |
|---|---|---|
| `--mode` | yes | `count` / `hours` / `since` |
| `--value` | yes | int for `count`/`hours`, `"YYYY-MM-DD HH:MM"` for `since` |
| `--engine` | no | `openrouter` (default) / `groq` / `claude` / `ollama` |

---

## What I'd do in future iterations

- **Persistent listener + SQLite** — instead of re-fetching every run, keep a background process that stores new messages incrementally; summarize from the local DB.
- **`/summarize` on-demand command** — turn it into a proper Telegram bot command so any group member can trigger a summary without touching the terminal.
- **Multi-group support** — one config file, many source groups, routing summaries to different destinations.
- **Consolidate env var naming** — replace the `_DIEGO` / `_DIGG15` suffixes with a single `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` pair so forking doesn't require editing variable names.
- **Streaming output** — for long summaries, stream the LLM response directly into Telegram instead of waiting for the full completion.

---

## License

MIT
