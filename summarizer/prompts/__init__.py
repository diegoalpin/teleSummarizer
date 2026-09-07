"""
Registry of prompt builders. Each module exposes `build(messages, label) -> str`.
Adding a new prompt style is a new module here plus one line in REGISTRY.
"""
from . import general, stocks

REGISTRY = {
    general.NAME: general.build,
    stocks.NAME: stocks.build,
}


def get(name: str):
    try:
        return REGISTRY[name]
    except KeyError:
        raise ValueError(f"Unknown prompt: {name!r}. Available: {', '.join(REGISTRY)}")
