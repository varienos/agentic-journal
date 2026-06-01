from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from agent_journal.security import redact_value

SCHEMA_VERSION = 1

ALLOWED_EVENT_TYPES = {
    "agent_start",
    "agent_end",
    "git_commit",
    "verification",
    "semantic_note",
    "session_summary",
    "task_completed_claim",
    "task_blocked",
}


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    event = redact_value(dict(raw))
    event_type = event.get("event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"Unsupported event_type: {event_type!r}")

    normalized: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event.get("event_id") or str(uuid4()),
        "ts": event.get("ts") or datetime.now().astimezone().isoformat(timespec="seconds"),
        "event_type": event_type,
        "agent": event.get("agent"),
        "session_id": event.get("session_id"),
        "cwd": event.get("cwd"),
        "repo": event.get("repo"),
        "branch": event.get("branch"),
        "commit": event.get("commit"),
        "command": event.get("command"),
        "exit_code": event.get("exit_code"),
        "duration_ms": event.get("duration_ms"),
        "files_changed": event.get("files_changed") or [],
        "semantic": event.get("semantic") or {},
        "evidence": event.get("evidence") or {},
    }

    return {key: value for key, value in normalized.items() if value is not None}
