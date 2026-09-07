"""
Indonesian stock-market group summarizer — ticker-organized, slang-aware.
See summarizer/ for the actual implementation.

Usage:
  python EdSum.py --last 200                            # last 200 messages, openrouter (default)
  python EdSum.py --last 12h --engine claude             # last 12 hours
  python EdSum.py --last 1w --to "@someone"              # last week, sent as a DM
  python EdSum.py --since "2024-01-15 09:00"

Setup:
  pip install telethon groq anthropic requests python-dotenv
"""
from summarizer.cli import main

DEFAULT_GROUP = "Social Trade Exclusive"

if __name__ == "__main__":
    main(
        prompt_name="stocks",
        default_group=DEFAULT_GROUP,
        description="Indonesian stock-market Telegram group summarizer",
    )
