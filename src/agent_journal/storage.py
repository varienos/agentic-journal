from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from agent_journal.config import ensure_config, journal_root


def _date_from_ts(ts: str) -> str:
    return ts[:10]


def append_jsonl_event(root: str | Path, event: dict[str, Any]) -> Path:
    root_path = Path(root).expanduser()
    date = _date_from_ts(event["ts"])
    event_dir = root_path / "events"
    event_dir.mkdir(parents=True, exist_ok=True)
    path = event_dir / f"{date}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return path


def read_jsonl_events(path: str | Path) -> Iterable[dict[str, Any]]:
    jsonl_path = Path(path)
    if not jsonl_path.exists():
        return []
    events = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def db_file(root: str | Path | None = None) -> Path:
    return Path(root).expanduser() / "agent-journal.db" if root else journal_root() / "agent-journal.db"


def connect(root: str | Path | None = None) -> sqlite3.Connection:
    path = db_file(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(root: str | Path | None = None) -> Path:
    path = db_file(root)
    ensure_config(path.parent)
    with connect(root) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY,
              schema_version INTEGER NOT NULL,
              ts TEXT NOT NULL,
              event_type TEXT NOT NULL,
              agent TEXT,
              session_id TEXT,
              cwd TEXT,
              repo TEXT,
              branch TEXT,
              commit_hash TEXT,
              exit_code INTEGER,
              duration_ms INTEGER,
              raw_json TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_repo ON events(repo)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_agent ON events(agent)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
    return path


def insert_event(root: str | Path | None, event: dict[str, Any]) -> None:
    init_db(root)
    with connect(root) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO events (
              event_id, schema_version, ts, event_type, agent, session_id, cwd,
              repo, branch, commit_hash, exit_code, duration_ms, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["schema_version"],
                event["ts"],
                event["event_type"],
                event.get("agent"),
                event.get("session_id"),
                event.get("cwd"),
                event.get("repo"),
                event.get("branch"),
                event.get("commit"),
                event.get("exit_code"),
                event.get("duration_ms"),
                json.dumps(event, ensure_ascii=False, sort_keys=True),
            ),
        )


def write_event(root: str | Path | None, event: dict[str, Any]) -> Path:
    root_path = Path(root).expanduser() if root else journal_root()
    insert_event(root_path, event)
    return append_jsonl_event(root_path, event)


def read_events_for_date(root: str | Path | None, date: str | None) -> list[dict[str, Any]]:
    root_path = Path(root).expanduser() if root else journal_root()
    init_db(root_path)
    query = "SELECT raw_json FROM events"
    params: tuple[str, ...] = ()
    if date:
        query += " WHERE ts LIKE ?"
        params = (f"{date}%",)
    query += " ORDER BY ts, event_id"
    with connect(root_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [json.loads(row["raw_json"]) for row in rows]
