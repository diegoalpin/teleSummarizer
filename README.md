# teleSummarizer

Summarize Telegram group chats with a switchable LLM backend (Groq, Claude, or local Ollama). Built for high-volume groups where reading every message isn't realistic — point it at a chat, pick a window, get a structured summary in your Telegram Saved Messages.

The repo ships with **two summarizers**:

- **`TeleSummarizer.py`** — general-purpose. Produces topic-organized summaries with attribution (who said what, follow-ups, links shared).
- **`EdSum.py`** — specialized for **Indonesian stock market discussions**. Produces ticker-first summaries (e.g. `BBRI`, `BBCA`) with sentiment, theses, an Indonesian-slang glossary baked into the prompt, and special highlighting for a designated key contributor.

Both share the same Telethon fetching logic, CLI, and engine-routing code — only the prompt and a few config values differ.

---

## Features

- **Three time-window modes**: last N messages (`count`), last N hours (`hours`), or since a specific datetime (`since`).
- **Three LLM engines, swappable via CLI flag**:
  - `groq` — `llama-3.3-70b-versatile` (fast, free tier)
  - `claude` — `claude-haiku-4-5` (cheap, high quality)
  - `ollama` — local `mistral` (fully offline, zero cost)
- **Telethon user client** — reads any group you're a member of, including private ones (bots can't do this).
- **Output to Saved Messages** — summary lands in your own "me" chat, formatted with metadata (group name, timestamp, message count, engine used).
- **Two prompt templates** — pick the script that matches your use case, or fork either as a starting point for your own.

---

## How it works

```
┌─────────────────────┐
│   Telegram Group    │
└──────────┬──────────┘
           │ Telethon (your user account)
           ▼
┌─────────────────────┐
│  fetch_by_count /   │     ── messages collected in-memory ──
│  fetch_by_time      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   build_prompt      │     ── EdSum: ticker-first / Indonesian
│                     │     ── TeleSummarizer: topic + attribution
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Groq / Claude /    │
│  Ollama             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Telegram Saved     │
│  Messages ("me")    │
└─────────────────────┘
```

It's a single-shot script: each run authenticates, fetches, summarizes, sends, exits. No background listener, no database. Schedule it with cron / Task Scheduler if you want recurring summaries.

---

## File overview

| File | Purpose |
|---|---|
| `TeleSummarizer.py` | General-purpose summarizer with topic + attribution prompt. |
| `EdSum.py` | Indonesian stock market summarizer (ticker-first, slang-aware). |
| `slang_glossary.py` | Indonesian stock market slang dictionary, imported by `EdSum.py` via `format_slang_for_prompt()`. *(Not yet pushed — required for `EdSum.py` to run.)* |
| `tg_session.session` | Telethon auth session, auto-created on first run. **Gitignored.** |
| `.env` | API credentials. **Gitignored.** |

---

## Requirements

- Python 3.10+
- A Telegram account (this uses a Telethon **user client**, not a bot)
- Telegram API credentials from [my.telegram.org](https://my.telegram.org)
- API key for at least one LLM provider you intend to use

```bash
pip install telethon groq anthropic requests python-dotenv
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/diegoalpin/teleSummarizer.git
cd teleSummarizer
pip install telethon groq anthropic requests python-dotenv
```

### 2. Create `.env`

The two scripts currently read **different** env var names. Set whichever pair matches the script you'll run:

```env
# Used by EdSum.py
TELEGRAM_API_ID_DIGG15=1234567
TELEGRAM_API_HASH_DIGG15=your_api_hash_here

# Used by TeleSummarizer.py
TELEGRAM_API_ID_DIEGO=1234567
TELEGRAM_API_HASH_DIEGO=your_api_hash_here

# LLM keys (only fill what you'll use)
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
```

> **Heads up:** the env var names are tied to specific Telegram phone-number accounts (`DIGG15`, `DIEGO`). If you fork this repo, you'll likely want to consolidate them to a single `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` pair.

> **Also note:** `ANTHROPIC_API_KEY` is currently hardcoded as `""` in both scripts rather than read from `.env`. To use the `claude` engine, change `ANTHROPIC_API_KEY = ""` to `ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")` near the top of each file.

### 3. Set the target group

In the script you're using, edit `GROUP_NAME` to the (case-insensitive, partial-match-ok) name of your target group:

```python
GROUP_NAME = "Social Trade Exclusive"
```

The script does a substring match against your dialog list, so `"social trade"` will also work.

### 4. First run — Telethon auth

```bash
python TeleSummarizer.py --mode count --value 50
```

Telethon will prompt for your phone number and a code from Telegram. After that, `tg_session.session` is saved and reused automatically.

---

## Usage

### General-purpose summarizer

```bash
# Last 200 messages, via Groq
python TeleSummarizer.py --mode count --value 200 --engine groq

# Last 6 hours, via Claude
python TeleSummarizer.py --mode hours --value 6 --engine claude

# Since a specific datetime (UTC), via local Ollama
python TeleSummarizer.py --mode since --value "2026-01-15 09:00" --engine ollama
```

### Indonesian stock market summarizer

```bash
python EdSum.py --mode hours --value 24 --engine groq
```

Same flags. The difference is entirely in the prompt — `EdSum.py` reorganizes output by stock ticker, tags each ticker with sentiment, applies an Indonesian slang glossary, and surfaces messages from a designated key contributor (hardcoded user ID `1200423176`) with a ⭐ marker.

### CLI reference

| Flag | Required | Values | Notes |
|---|---|---|---|
| `--mode` | yes | `count` / `hours` / `since` | How to select messages |
| `--value` | yes | depends on mode | int for `count`/`hours`, `"YYYY-MM-DD HH:MM"` for `since` |
| `--engine` | no | `groq` / `claude` / `ollama` | Default: `groq` |

### Scheduling

**Linux / macOS — cron, daily at 08:00:**
```cron
0 8 * * * cd /path/to/teleSummarizer && /usr/bin/python3 EdSum.py --mode hours --value 24 --engine groq
```

**Windows — Task Scheduler:**
```cmd
schtasks /create ^
  /tn "TelegramSummarizer" ^
  /tr "python C:\path\to\teleSummarizer\EdSum.py --mode hours --value 24 --engine groq" ^
  /sc daily ^
  /st 08:00 ^
  /f
```

---

## Output

The summary is posted to your **Telegram Saved Messages** (the "me" chat) with a header showing the group, timestamp, message count, and engine used.

### `TeleSummarizer.py` (general)

```
📋 Group Summary — My Dev Group
🕐 2026-05-06 08:00  |  📝 142 messages  |  ⚙️ groq

📌 TOPICS
• Alice and Bob debated the deployment timeline, settling on Friday.
• The group discussed which framework to use for the frontend.
• Carol asked about the API budget; no conclusion reached.

🔗 LINKS & MEDIA
• Dave shared a link to the new Figma mockups.

⚠️ FOLLOW-UPS
• Carol's question about the API budget is unresolved.
• Alice and Bob to confirm deployment date.
```

### `EdSum.py` (Indonesian stocks)

```
📋 Group Summary — Social Trade Exclusive
🕐 2026-05-06 08:00  |  📝 487 messages  |  ⚙️ groq

📈 BBRI
  Sentiment: Bullish
  Key idea: Q4 earnings beat plus dividend hike speculation.
  Discussion: Members flagged the buyback announcement and unusual
  call option volume. Targets cited: 5,800 short-term, 6,200 on
  follow-through.
  ⭐ Key contributor's view: Adding on dips below 5,500.

📈 BBCA
  Sentiment: Mixed
  ...

🌐 MACRO & GENERAL
  Rate cut expectations pushed to Q3. Sector rotation discussion
  favoured banks over commodities.

⚠️ OPEN IDEAS & FOLLOW-UPS
  • TLKM earnings next Tuesday — flagged for re-review
```

---

## Choosing an engine

| Engine | Model | Best for | Cost | Latency |
|---|---|---|---|---|
| `groq` | `llama-3.3-70b-versatile` | Daily scheduled runs, high volume | Free tier, then cheap | Very fast |
| `claude` | `claude-haiku-4-5` | High-stakes / nuanced summaries | Low | Moderate |
| `ollama` | `mistral` (local) | Privacy-sensitive content, offline | Free | Hardware-dependent |

Default is `groq` — right tradeoff for "fresh summary every morning at ~zero cost." Switch to `claude` when the day's content is dense or stakes are high. Use `ollama` when message content shouldn't leave your machine.

---

## Customizing for your own group

The two scripts are deliberately small (~250 lines each) and hackable. The most common changes:

- **Change the prompt** — edit `build_prompt()` in either script. That's where the personality of the summary lives.
- **Change the destination** — replace `tg.send_message("me", ...)` with a group ID or username to post elsewhere.
- **Change the key contributor** (`EdSum.py` only) — search for the user ID `1200423176` in `EdSum.py` and replace with your own (or remove the special-handling block entirely).
- **Add a new engine** — drop in a new `summarize_xyz()` function and add it to the `ENGINE_MODELS` dict and the dispatcher in `summarize()`.

---

## Privacy & responsible use

This tool uses your **personal Telegram account** via Telethon, not a bot. That means:

- It can read any group you're a member of, including private ones — only summarize groups where members would expect this, or get explicit consent.
- LLM API calls send raw message content to the chosen provider. Ollama is the only fully-local option.
- Session files, env files, and any future databases should stay gitignored. Never commit them.
- Nothing produced by this tool is investment advice. Summaries reflect what was *said* in chat, not what is *true*.

---

## Roadmap

- [ ] Push `slang_glossary.py` (required for `EdSum.py`)
- [ ] Consolidate env var naming (`TELEGRAM_API_ID` / `TELEGRAM_API_HASH`)
- [ ] Wire `ANTHROPIC_API_KEY` to `os.getenv()` instead of hardcoded empty string
- [ ] Persistent listener + SQLite store (so summaries don't re-fetch every run)
- [ ] On-demand `/summarize` command via Telegram chat
- [ ] Multi-group support (one config, many sources)

---

## License

MIT