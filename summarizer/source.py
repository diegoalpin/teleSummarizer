"""
Everything that reads from Telegram: connecting, resolving the target chat,
and pulling messages into a source-agnostic Message record.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from telethon import TelegramClient

from .timeframe import Timeframe


@dataclass
class Message:
    sender_id: Optional[int]
    sender_name: str
    text: str
    timestamp: datetime

    def as_prompt_line(self) -> str:
        return f"{self.sender_name}: {self.text}"


async def find_group(client: TelegramClient, name: str):
    """Fuzzy, case-insensitive match against the user's dialog list."""
    async for dialog in client.iter_dialogs():
        if name.lower() in dialog.name.lower():
            return dialog
    return None


async def _resolve_sender(msg) -> tuple:
    try:
        sender = await msg.get_sender()
        return sender.id, (sender.first_name or "Unknown")
    except Exception:
        return None, "Unknown"


async def fetch_messages(client: TelegramClient, entity, frame: Timeframe) -> List[Message]:
    """Fetch messages according to a TimeFrame (either a count or a since-instant)."""
    if frame.kind == "count":
        return await _fetch_by_count(client, entity, frame.count)
    return await _fetch_by_time(client, entity, frame.since)


async def _fetch_by_count(client: TelegramClient, entity, count: int) -> List[Message]:
    messages: List[Message] = []
    async for msg in client.iter_messages(entity, limit=count):
        if msg.text:
            sender_id, sender_name = await _resolve_sender(msg)
            messages.append(Message(sender_id, sender_name, msg.text, msg.date))
    messages.reverse()
    return messages


async def _fetch_by_time(client: TelegramClient, entity, since: datetime) -> List[Message]:
    messages: List[Message] = []
    async for msg in client.iter_messages(entity, offset_date=since, reverse=True):
        if msg.text:
            sender_id, sender_name = await _resolve_sender(msg)
            messages.append(Message(sender_id, sender_name, msg.text, msg.date))
    return messages
