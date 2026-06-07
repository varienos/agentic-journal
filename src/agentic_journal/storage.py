from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from agentic_journal.config import ensure_config, journal_root, secure_dir, secure_file
from agentic_journal.events import SCHEMA_VERSION


def _date_from_ts(ts: str) -> str:
    date = ts[:10]
    if "/" in date or "\\" in date or ".." in date:
        raise ValueError(f"Unsafe ts for date routing: {ts!r}")
    return date


def append_jsonl_event(root: str | Path, event: dict[str, Any]) -> Path:
    root_path = Path(root).expanduser()
    date = _date_from_ts(event["ts"])
    event_dir = secure_dir(root_path / "events")
    path = event_dir / f"{date}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    secure_file(path)
    return path


def read_jsonl_events(path: str | Path) -> Iterable[dict[str, Any]]:
    jsonl_path = Path(path)
    if not jsonl_path.exists():
        return []
    events = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # Skip a torn or corrupt line (e.g. after a crash mid-append) rather
            # than failing the whole read; the SQLite store is the primary path.
            continue
    return events


def db_file(root: str | Path | None = None) -> Path:
    return Path(root).expanduser() / "agentic-journal.db" if root else journal_root() / "agentic-journal.db"


def connect(root: str | Path | None = None) -> sqlite3.Connection:
    path = db_file(root)
    secure_dir(path.parent)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_to_1(conn: sqlite3.Connection) -> None:
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
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id)")


MIGRATIONS = {
    1: _migrate_to_1,
}


def _apply_migrations(conn: sqlite3.Connection) -> None:
    current_version = conn.execute("PRAGMA user_version").fetchone()[0]
    if current_version > SCHEMA_VERSION:
        return
    for version in range(current_version + 1, SCHEMA_VERSION + 1):
        migration = MIGRATIONS[version]
        migration(conn)
        conn.execute(f"PRAGMA user_version = {version}")


def init_db(root: str | Path | None = None) -> Path:
    path = db_file(root)
    ensure_config(path.parent)
    with connect(root) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        _apply_migrations(conn)
    secure_file(path)
    # WAL mode creates `-wal` / `-shm` sidecars that hold the freshest, not-yet
    # checkpointed event data; restrict them to the owner as well.
    for suffix in ("-wal", "-shm"):
        sidecar = path.with_name(path.name + suffix)
        if sidecar.exists():
            secure_file(sidecar)
    return path


def insert_event(root: str | Path | None, event: dict[str, Any]) -> bool:
    init_db(root)
    with connect(root) as conn:
        cursor = conn.execute(
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
        return cursor.rowcount > 0


def delete_event(root: str | Path | None, event_id: str) -> None:
    with connect(root) as conn:
        conn.execute("DELETE FROM events WHERE event_id = ?", (event_id,))


def write_event(root: str | Path | None, event: dict[str, Any]) -> Path:
    root_path = Path(root).expanduser() if root else journal_root()
    path = root_path / "events" / f"{_date_from_ts(event['ts'])}.jsonl"
    if insert_event(root_path, event):
        try:
            return append_jsonl_event(root_path, event)
        except OSError:
            # Keep SQLite (read path) and the JSONL mirror consistent: if the
            # mirror append fails, roll back the SQLite row so a retry re-attempts
            # both writes instead of permanently skipping the mirror line.
            try:
                delete_event(root_path, event["event_id"])
            except Exception:
                # SQLite is the primary read path. If rollback also fails, keep
                # surfacing the original append error; masking it would make the
                # actionable filesystem failure harder to diagnose.
                pass
            raise
    return path


def _rows_to_events(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    events = []
    for row in rows:
        event = json.loads(row["raw_json"])
        if event.get("schema_version", 0) > SCHEMA_VERSION:
            continue
        events.append(event)
    return events


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
    return _rows_to_events(rows)


def read_events_for_session(root: str | Path | None, session_id: str) -> list[dict[str, Any]]:
    """Read every event for one session across all dates, using the index.

    The session guard needs to see a session that may span local midnight, so it
    cannot scope to a single date; querying by the indexed ``session_id`` avoids
    a full-table scan of the entire journal history on every session exit.
    """
    root_path = Path(root).expanduser() if root else journal_root()
    init_db(root_path)
    with connect(root_path) as conn:
        rows = conn.execute(
            "SELECT raw_json FROM events WHERE session_id = ? ORDER BY ts, event_id",
            (session_id,),
        ).fetchall()
    return _rows_to_events(rows)
