import pytest

from agent_journal import storage
from agent_journal.storage import (
    append_jsonl_event,
    init_db,
    insert_event,
    read_events_for_date,
    read_events_for_session,
    read_jsonl_events,
    write_event,
)


def _event(event_id, ts="2026-05-31T10:00:00+03:00", **updates):
    raw = {
        "schema_version": 1,
        "event_id": event_id,
        "ts": ts,
        "event_type": "agent_start",
        "agent": "codex",
        "semantic": {},
        "evidence": {},
    }
    raw.update(updates)
    return raw


def test_append_jsonl_event_writes_by_date(tmp_path):
    root = tmp_path / "journal"
    event = {
        "schema_version": 1,
        "event_id": "e1",
        "ts": "2026-05-31T10:00:00+03:00",
        "event_type": "agent_start",
        "agent": "codex",
    }

    path = append_jsonl_event(root, event)

    assert path == root / "events" / "2026-05-31.jsonl"
    assert list(read_jsonl_events(path)) == [event]


def test_sqlite_storage_uses_wal_and_reads_by_date(tmp_path):
    root = tmp_path / "journal"
    db_path = init_db(root)
    event = {
        "schema_version": 1,
        "event_id": "e1",
        "ts": "2026-05-31T10:00:00+03:00",
        "event_type": "agent_start",
        "agent": "codex",
        "semantic": {},
        "evidence": {},
    }

    insert_event(root, event)
    insert_event(root, event)

    events = read_events_for_date(root, "2026-05-31")
    assert db_path.exists()
    assert len(events) == 1
    assert events[0]["event_id"] == "e1"


def test_write_event_keeps_jsonl_mirror_idempotent(tmp_path):
    from agent_journal.storage import write_event

    root = tmp_path / "journal"
    event = {
        "schema_version": 1,
        "event_id": "e1",
        "ts": "2026-05-31T10:00:00+03:00",
        "event_type": "agent_start",
        "agent": "codex",
        "semantic": {},
        "evidence": {},
    }

    path = write_event(root, event)
    second_path = write_event(root, event)

    assert second_path == path
    assert list(read_jsonl_events(path)) == [event]
    assert len(read_events_for_date(root, "2026-05-31")) == 1


def test_write_event_rolls_back_sqlite_when_jsonl_append_fails(tmp_path, monkeypatch):
    root = tmp_path / "journal"

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(storage, "append_jsonl_event", boom)

    with pytest.raises(OSError):
        write_event(root, _event("e1"))

    # The SQLite row must be rolled back so a retry re-attempts both writes
    # instead of permanently skipping the JSONL mirror line.
    assert read_events_for_date(root, "2026-05-31") == []


def test_write_event_preserves_original_append_error_when_rollback_fails(tmp_path, monkeypatch):
    root = tmp_path / "journal"

    def append_boom(*args, **kwargs):
        raise OSError("jsonl append failed")

    def delete_boom(*args, **kwargs):
        raise OSError("rollback failed")

    monkeypatch.setattr(storage, "append_jsonl_event", append_boom)
    monkeypatch.setattr(storage, "delete_event", delete_boom)

    with pytest.raises(OSError, match="jsonl append failed"):
        write_event(root, _event("e1"))


def test_init_db_tracks_schema_user_version(tmp_path):
    root = tmp_path / "journal"

    init_db(root)

    with storage.connect(root) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == 1


def test_read_events_skips_future_schema_versions(tmp_path):
    root = tmp_path / "journal"
    future = _event("future", schema_version=999)
    current = _event("current")

    write_event(root, future)
    write_event(root, current)

    events = read_events_for_date(root, "2026-05-31")

    assert [event["event_id"] for event in events] == ["current"]


def test_write_event_appends_multiple_events_in_order(tmp_path):
    root = tmp_path / "journal"
    path = write_event(root, _event("e1", ts="2026-05-31T10:00:00+03:00"))
    write_event(root, _event("e2", ts="2026-05-31T11:00:00+03:00"))

    ids = [event["event_id"] for event in read_jsonl_events(path)]
    assert ids == ["e1", "e2"]


def test_read_events_for_session_filters_by_session_across_dates(tmp_path):
    root = tmp_path / "journal"
    write_event(root, _event("a1", ts="2026-05-31T23:59:00+03:00", session_id="s1"))
    write_event(root, _event("a2", ts="2026-06-01T00:01:00+03:00", session_id="s1"))
    write_event(root, _event("b1", ts="2026-06-01T00:02:00+03:00", session_id="s2"))

    events = read_events_for_session(root, "s1")

    assert [event["event_id"] for event in events] == ["a1", "a2"]


def test_write_event_secures_db_and_wal_sidecar_permissions(tmp_path):
    import glob
    import os
    import stat

    root = tmp_path / "journal"
    write_event(root, _event("e1"))

    db_files = glob.glob(str(root / "agent-journal.db*"))
    assert any(name.endswith("agent-journal.db") for name in db_files)
    for path in db_files:
        mode = stat.S_IMODE(os.stat(path).st_mode)
        assert mode == 0o600, (os.path.basename(path), oct(mode))


def test_read_jsonl_events_skips_corrupt_lines(tmp_path):
    path = tmp_path / "2026-05-31.jsonl"
    good = '{"event_id": "ok", "event_type": "agent_start"}'
    path.write_text(good + "\n{ this is not json\n", encoding="utf-8")

    events = list(read_jsonl_events(path))

    assert events == [{"event_id": "ok", "event_type": "agent_start"}]
