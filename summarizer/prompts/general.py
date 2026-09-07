"""Topic-organized summary with per-topic attribution. Used by TeleSummarizer.py."""
from typing import List

from ..source import Message

NAME = "general"


def build(messages: List[Message], label: str) -> str:
    combined = "\n".join(m.as_prompt_line() for m in messages)
    return (
        f"You are summarizing a Telegram group chat ({label}).\n"
        "Be concise and structured. For each topic, attribute it to the person or people involved.\n"
        "Follow these rules for attribution:\n"
        "- If only 1-2 people discuss a topic, name them: e.g. 'Alice and Bob discussed...'\n"
        "- If 3+ people are involved, summarize as a group: e.g. 'The group discussed...'\n"
        "- If someone asks a question, attribute it: e.g. 'Alice asked about...'\n"
        "- If someone shares a link or media, name them: e.g. 'Bob shared a link about...'\n"
        "- If someone makes a decision or conclusion, name them: e.g. 'Alice concluded...'\n\n"
        "Structure your summary as follows:\n\n"
        "📌 TOPICS\n"
        "For each topic, one bullet: who + what. Example:\n"
        "• Alice and Bob debated the project deadline, settling on Friday.\n"
        "• The group discussed weekend plans, with most leaning toward hiking.\n"
        "• Carol asked about the API budget; no conclusion reached.\n\n"
        "🔗 LINKS & MEDIA\n"
        "• List any links or media shared and who shared them. Skip if none.\n\n"
        "⚠️ FOLLOW-UPS\n"
        "• List open questions or action items and who they are assigned to. Skip if none.\n\n"
        f"Messages:\n{combined}\n\n"
        "Summary:"
    )
