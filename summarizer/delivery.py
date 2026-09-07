"""
Where the finished summary goes: Telegram message chunking (Telegram rejects
anything over 4096 UTF-16 units), destination resolution ("me", @username, a
phone number, or a fuzzy group name), and a console sink for dry runs.
"""
from typing import List

from telethon import TelegramClient

from . import config
from .source import find_group


def tg_len(text: str) -> int:
    """Telegram measures message length in UTF-16 code units, so emoji count as 2."""
    return len(text.encode("utf-16-le")) // 2


def split_for_telegram(text: str, limit: int = config.TELEGRAM_MAX_CHARS) -> List[str]:
    """Break a long message into Telegram-sized chunks, splitting on line boundaries."""
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


async def resolve_destination(client: TelegramClient, to: str):
    """
    Resolve a `--to` value into something Telethon's send_message accepts:
      - "me"                      -> Saved Messages
      - "@username" or a phone    -> passed straight through, Telethon resolves it
      - anything else             -> fuzzy-matched against the user's dialogs
                                      (same matching source.find_group uses for the
                                      fetch side), so "Family Chat" or "trading"
                                      works without knowing the exact chat name.
    """
    if to == "me" or to.startswith("@") or to.startswith("+"):
        return to

    dialog = await find_group(client, to)
    if dialog is None:
        raise ValueError(f"Could not resolve destination {to!r} to a chat, username, or phone number.")
    return dialog.entity


async def deliver(client: TelegramClient, to: str, text: str, dry_run: bool = False) -> int:
    """Send `text` to `to`, splitting into multiple messages if needed. Returns part count."""
    parts = split_for_telegram(text)

    if dry_run:
        for i, part in enumerate(parts, 1):
            header = f"----- DRY RUN: part {i}/{len(parts)} -> {to} -----" if len(parts) > 1 else f"----- DRY RUN -> {to} -----"
            print(header)
            print(part)
        return len(parts)

    entity = await resolve_destination(client, to)
    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            part = f"{part}\n\n— part {i}/{len(parts)} —"
        await client.send_message(entity, part)
    return len(parts)
