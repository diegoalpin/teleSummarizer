"""Wires fetch -> prompt -> engine -> delivery into one run."""
from datetime import datetime

from telethon import TelegramClient

from . import config, delivery, engines, prompts
from .source import fetch_messages, find_group
from .timeframe import Timeframe


async def run(
    group_name: str,
    timeframe: Timeframe,
    engine: str,
    prompt_name: str,
    to: str = "me",
    dry_run: bool = False,
) -> None:
    tg = TelegramClient(config.SESSION_NAME, config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
    await tg.start()

    print(f"\n📡 Finding group: {group_name}")
    target = await find_group(tg, group_name)
    if not target:
        print("❌ Group not found. Check the group name.")
        await tg.disconnect()
        return

    print(f"✅ Found: {target.name}")

    verb = "Fetching" if timeframe.kind == "count" else "Fetching messages from"
    print(f"\n📥 {verb} {timeframe.label}...")
    messages = await fetch_messages(tg, target.entity, timeframe)

    if not messages:
        print("⚠️  No messages found for the given range.")
        await tg.disconnect()
        return

    print(f"💬 {len(messages)} messages fetched.")

    print("\n🤖 Summarizing...")
    build_prompt = prompts.get(prompt_name)
    prompt = build_prompt(messages, timeframe.label)
    summary = engines.summarize(prompt, engine)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = (
        f"📋 **Group Summary — {target.name}**\n"
        f"🕐 {now_str}  |  📝 {len(messages)} messages  |  ⚙️ {engine}\n\n"
        f"{summary}"
    )

    part_count = await delivery.deliver(tg, to, full_message, dry_run=dry_run)

    suffix = f" in {part_count} messages" if part_count > 1 else ""
    destination_label = "console (dry run)" if dry_run else to
    print(f"\n✅ Summary sent to {destination_label}{suffix}!")

    await tg.disconnect()
