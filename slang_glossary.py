# slang_glossary.py

SLANG = {
    "cuan": "profit",
    "nyangkut": "stuck in a losing position",
    "gorengan": "manipulated/pump-and-dump stock",
    "bandar": "market maker or big player manipulating price",
    "ARA": "Auto Reject Atas (upper circuit breaker)",
    "ARB": "Auto Reject Bawah (lower circuit breaker)",
    "cut loss": "stop loss execution",
    "avg down": "averaging down on a position",
    "mantul": "bounce (from 'mental balik')",
}

def format_slang_for_prompt(slang: dict = SLANG) -> str:
    return "\n".join(f"- '{k}' = {v}" for k, v in slang.items())