"""
General-purpose Telegram group summarizer — topic-organized, with attribution.
See summarizer/ for the actual implementation.

Usage:
  python TeleSummarizer.py --group "My Dev Group" --last 200
  python TeleSummarizer.py --group "My Dev Group" --last 6h --engine claude
  python TeleSummarizer.py --group "My Dev Group" --since "2024-01-15 09:00" --engine ollama

Setup:
  pip install telethon groq anthropic requests python-dotenv
"""
from summarizer.cli import main

if __name__ == "__main__":
    main(
        prompt_name="general",
        default_group="",
        description="General-purpose Telegram group summarizer",
    )
