"""Ticker-organized summary with Indonesian slang awareness. Used by EdSum.py."""
from typing import List

from ..source import Message
from .slang import format_slang_for_prompt

NAME = "stocks"

# This sender's messages are marked with a ⭐ so the model surfaces them
# separately under each ticker, instead of merging them into group discussion.
KEY_CONTRIBUTOR_ID = 1200423176


def _format_line(m: Message) -> str:
    marker = "⭐ " if m.sender_id == KEY_CONTRIBUTOR_ID else ""
    return f"{marker}{m.sender_name}: {m.text}"


def build(messages: List[Message], label: str) -> str:
    combined = "\n".join(_format_line(m) for m in messages)
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

        "SPECIAL INSTRUCTION — Key Contributor:\n"
        "Messages prefixed with ⭐ are from a key contributor whose views carry higher weight.\n"
        "If a ⭐ message mentions a ticker, shares an analysis, or expresses a view,\n"
        "always highlight it explicitly with a ⭐ marker in your summary. Do not skip or merge their points into group discussion.\n\n"

        "SUMMARIZATION RULES:\n"
        "- Organize the summary by STOCK TICKER, not by person or chronology.\n"
        "- For each ticker: summarize the thesis, sentiment (bullish/bearish/neutral), key arguments, and any price levels or catalysts mentioned.\n"
        "- If no ticker is tied to a topic (e.g. macro discussion, strategy), group it under '🌐 MACRO & GENERAL'.\n"
        "- Attribution is secondary — only name someone if their view is notably distinct or if it's the key contributor.\n"
        "- If a ⭐ message discusses a ticker, always surface that view separately under that ticker.\n\n"

        "Structure your summary as follows:\n\n"

        "📈 [TICKER]\n"
        "  Sentiment: Bullish / Bearish / Mixed\n"
        "  Key idea: One-line thesis summary.\n"
        "  Discussion: 2–4 sentences summarizing the arguments, data points, or price levels discussed.\n"
        "  ⭐ Key contributor's view: [Only include if a ⭐ message covered this ticker. Closely paraphrase their point.]\n\n"

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
