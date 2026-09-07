# teleSummarizer

Summarize Telegram group chats with a switchable LLM backend. Point it at a group, pick a time window, get a structured summary sent wherever you want.

Ships with two thin entrypoints on top of a shared `summarizer/` package:
- **`TeleSummarizer.py`** — general-purpose, topic-organized with attribution
- **`EdSum.py`** — Indonesian stock market groups, ticker-first with sentiment and slang awareness

---

## How it works

```
Telegram Group → source.fetch_messages() → prompts.build() → engines.summarize() → delivery.deliver()
```

**Why Telethon (user client, not a bot):** bots can't read private groups. A user client can read any group you're a member of, which is the common case.

**Why four LLM engines:**
- `openrouter` (`openai/gpt-5.6-luna`, reasoning enabled) — **default.** Best summary quality; one key gets you any model OpenRouter hosts, so swapping models is a one-line change.
- `groq` (`llama-3.3-70b-versatile`) — free tier, very fast. Good fallback for high-frequency cron runs.
- `claude` (`claude-haiku-4-5`) — cheap and fast for dense or nuanced content.
- `ollama` (`mistral`, local) — fully offline; message content never leaves your machine.

**Why two entrypoints instead of one:** the prompt is the whole product. `TeleSummarizer.py` organizes by topic; `EdSum.py` reorganizes by stock ticker and bakes in an Indonesian slang glossary. Each is a ~20-line script that just points `summarizer.cli.main()` at its own prompt.

---

## Project layout

```
summarizer/
  config.py       env vars, per-engine model defaults, limits
  timeframe.py    "--last 1w" / "12h" / "200" / "--since ..." → a fetch instruction
  source.py       connects to Telegram, resolves the target chat, fetches Message objects
  engines.py      openrouter / groq / claude / ollama → summary text
  delivery.py     resolves "--to", chunks long summaries, sends (or prints, if --dry-run)
  prompts/
    general.py    topic-organized prompt (TeleSummarizer.py)
    stocks.py     ticker-organized prompt with slang glossary (EdSum.py)
    slang.py      Indonesian stock-market slang glossary
  pipeline.py     wires fetch → prompt → engine → delivery into one run
  cli.py          shared argparse, used by both entrypoints
EdSum.py           entrypoint: stocks prompt, defaults to the trading group
TeleSummarizer.py  entrypoint: general prompt, requires --group
```

Adding a third summarizer (a different chat, a different prompt style) is a new
`prompts/*.py` module plus a new ~20-line entrypoint — no copy-pasting the fetch,
engine, or delivery logic.

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

`EdSum.py` defaults to a hardcoded trading group; override it with `--group`.
`TeleSummarizer.py` has no default — pass `--group` every time:

```bash
python TeleSummarizer.py --group "My Group Name" --last 200   # case-insensitive, partial match OK
```

### 5. Run

```bash
# Last 200 messages via OpenRouter / GPT-5.6 Luna (default engine), to Saved Messages (default)
python EdSum.py --last 200

# Last 12 hours via Groq
python EdSum.py --last 12h --engine groq

# Last week, sent as a DM instead of Saved Messages
python EdSum.py --last 1w --to "@someone"

# Everything since a specific datetime (UTC), via local Ollama
python EdSum.py --since "2026-01-15 09:00" --engine ollama

# Preview the summary in the terminal without sending anything
python EdSum.py --last 50 --dry-run
```

On first run, Telethon will prompt for your phone number and a Telegram verification code. After that, `tg_session.session` is saved and reused automatically.

**CLI flags:**

| Flag | Required | Values |
|---|---|---|
| `--group` | `EdSum.py`: no (has a default) · `TeleSummarizer.py`: yes | partial group name, case-insensitive |
| `--last` | one of `--last` / `--since` / legacy `--mode`+`--value` | a message count (`200`) or duration (`30m`, `12h`, `3d`, `1w`) |
| `--since` | | `"YYYY-MM-DD HH:MM"`, interpreted as UTC |
| `--engine` | no | `openrouter` (default) / `groq` / `claude` / `ollama` |
| `--to` | no | `"me"` (default, Saved Messages) / `"@username"` / phone number / group name |
| `--dry-run` | no | print the summary to the console instead of sending it |

The original `--mode {count,hours,since} --value X` flags still work as aliases for `--last`/`--since`, so existing scripts (like `run.sh`) don't need to change.

---

## What I'd do in future iterations

- **Persistent listener + SQLite** — instead of re-fetching every run, keep a background process that stores new messages incrementally; summarize from the local DB.
- **`/summarize` on-demand command** — turn it into a proper Telegram bot command so any group member can trigger a summary without touching the terminal.
- **Multi-group, multi-destination config** — one config file, many source groups, each routed to its own `--to`.
- **Streaming output** — for long summaries, stream the LLM response directly into Telegram instead of waiting for the full completion.

---

## License

MIT
