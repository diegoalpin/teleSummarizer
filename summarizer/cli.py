"""
Shared argparse wiring for both entrypoints. Each entrypoint just supplies
its prompt name, default group, and description.
"""
import argparse
import asyncio

from . import config, timeframe
from .pipeline import run


def _build_parser(description: str, default_group: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)

    if default_group:
        parser.add_argument(
            "--group", default=default_group,
            help=f"Telegram group to summarize, partial name OK (default: {default_group!r})"
        )
    else:
        parser.add_argument(
            "--group", required=True,
            help="Telegram group to summarize, partial name OK"
        )
    parser.add_argument(
        "--last",
        help="How much history to pull: a message count ('200') or a duration "
             "('30m', '12h', '3d', '1w')"
    )
    parser.add_argument(
        "--since",
        help='Pull everything since this UTC datetime: "YYYY-MM-DD HH:MM"'
    )

    # Back-compat with the original --mode/--value flags.
    parser.add_argument("--mode", choices=["count", "hours", "since"], help=argparse.SUPPRESS)
    parser.add_argument("--value", help=argparse.SUPPRESS)

    parser.add_argument(
        "--engine", choices=list(config.ENGINE_MODELS), default="openrouter",
        help="AI engine to use for summarization (default: openrouter)"
    )
    parser.add_argument(
        "--to", default="me",
        help='Where to send the summary: "me" (Saved Messages, default), "@username", '
             "a phone number, or a group name"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the summary to the console instead of sending it to Telegram"
    )

    return parser


def _resolve_frame(args) -> timeframe.Timeframe:
    if args.mode or args.value:
        if not (args.mode and args.value):
            raise SystemExit("--mode and --value must be given together")
        return timeframe.from_legacy(args.mode, args.value)

    if args.since:
        return timeframe.parse_since(args.since)

    if args.last:
        return timeframe.parse_last(args.last)

    raise SystemExit("Specify one of --last, --since, or the legacy --mode/--value")


def main(prompt_name: str, default_group: str, description: str) -> None:
    parser = _build_parser(description, default_group)
    args = parser.parse_args()
    frame = _resolve_frame(args)

    asyncio.run(run(
        group_name=args.group,
        timeframe=frame,
        engine=args.engine,
        prompt_name=prompt_name,
        to=args.to,
        dry_run=args.dry_run,
    ))
