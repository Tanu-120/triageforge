"""Redact PII *before* text ever reaches a model (data-minimisation boundary)."""

import re

_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "CARD": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "PHONE": re.compile(r"(?<!\w)\+?\d[\d\s().-]{8,14}\d(?!\w)"),
}


def redact(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for label, pat in _PATTERNS.items():
        text, n = pat.subn(f"[{label}]", text)
        if n:
            counts[label.lower()] = n
    return text, counts
