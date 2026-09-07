"""
Turn a CLI-friendly string into a concrete fetch instruction: either "last N
messages" or "everything since some UTC instant". Both the modern `--last` /
`--since` flags and the legacy `--mode` / `--value` pair resolve to the same
TimeFrame, so the rest of the pipeline only has to know about one shape.
"""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

_UNITS = {
    "m": timedelta(minutes=1),
    "h": timedelta(hours=1),
    "d": timedelta(days=1),
    "w": timedelta(weeks=1),
}
_RELATIVE_RE = re.compile(r"^(\d+(?:\.\d+)?)([mhdw])$")


@dataclass
class Timeframe:
    kind: str            # "count" or "range"
    label: str            # human-readable, used in the prompt and the delivered message
    count: Optional[int] = None
    since: Optional[datetime] = None


def parse_last(value: str) -> Timeframe:
    """
    Parse a `--last` value:
      - a bare integer means "last N messages", e.g. "200"
      - a number + unit means "messages from the last <duration>", e.g.
        "30m", "12h", "3d", "1w"
    """
    value = value.strip()

    if value.isdigit():
        count = int(value)
        return Timeframe(kind="count", count=count, label=f"last {count} messages")

    match = _RELATIVE_RE.match(value)
    if not match:
        raise ValueError(
            f"Invalid --last value: {value!r}. Use a message count (e.g. '200') "
            "or a duration like '30m', '12h', '3d', '1w'."
        )

    amount, unit = match.groups()
    delta = _UNITS[unit] * float(amount)
    since = datetime.now(timezone.utc) - delta

    unit_label = {"m": "minute", "h": "hour", "d": "day", "w": "week"}[unit]
    amount_display = amount.rstrip("0").rstrip(".") if "." in amount else amount
    plural = "" if amount_display == "1" else "s"

    return Timeframe(kind="range", since=since, label=f"last {amount_display} {unit_label}{plural}")


def parse_since(value: str) -> Timeframe:
    """Parse an absolute `--since "YYYY-MM-DD HH:MM"` value, interpreted as UTC."""
    since_dt = datetime.strptime(value, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return Timeframe(kind="range", since=since_dt, label=f"since {value} UTC")


def from_legacy(mode: str, value: str) -> Timeframe:
    """Back-compat shim for the original `--mode {count,hours,since} --value X` flags."""
    if mode == "count":
        return parse_last(value)
    if mode == "hours":
        return parse_last(f"{value}h")
    if mode == "since":
        return parse_since(value)
    raise ValueError(f"Unknown mode: {mode}")
