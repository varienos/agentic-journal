from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|token|secret|password|authorization|credential)",
    re.IGNORECASE,
)
BEARER_RE = re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
ASSIGNMENT_SECRET_RE = re.compile(
    r"\b([A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*)=([^\s]+)",
    re.IGNORECASE,
)
LONG_TOKEN_RE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{8,}|[A-Za-z0-9_-]{32,})\b")


def redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if SECRET_KEY_RE.search(str(key)):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_value(item)
        return redacted
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, str):
        value = BEARER_RE.sub(r"\1[REDACTED]", value)
        value = ASSIGNMENT_SECRET_RE.sub(r"\1=[REDACTED]", value)
        value = LONG_TOKEN_RE.sub("[REDACTED]", value)
        return value
    return value

