from agent_journal.storage import (
    append_jsonl_event,
    init_db,
    insert_event,
    read_jsonl_events,
    read_events_for_date,
)


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

