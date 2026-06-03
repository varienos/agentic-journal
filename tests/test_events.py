import pytest

from agent_journal.config import DEFAULT_CONFIG
from agent_journal.events import MAX_SEMANTIC_TEXT, SCHEMA_VERSION, normalize_event


def test_normalize_event_adds_required_fields():
    event = normalize_event({"event_type": "agent_start", "agent": "codex"})

    assert event["schema_version"] == 1
    assert event["event_id"]
    assert event["ts"]
    assert event["event_type"] == "agent_start"
    assert event["agent"] == "codex"
    assert event["semantic"] == {}
    assert event["evidence"] == {}


def test_default_config_schema_version_matches_event_schema_version():
    assert f"schema_version = {SCHEMA_VERSION}" in DEFAULT_CONFIG


def test_normalize_event_rejects_unknown_event_type():
    try:
        normalize_event({"event_type": "unknown", "agent": "codex"})
    except ValueError as exc:
        assert "event_type" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_normalize_event_redacts_sensitive_values():
    event = normalize_event(
        {
            "event_type": "semantic_note",
            "agent": "claude",
            "semantic": {"note": "Authorization: Bearer secret-token-value"},
        }
    )

    assert "secret-token-value" not in event["semantic"]["note"]


def test_normalize_event_preserves_commit_hashes():
    commit = "a" * 40

    event = normalize_event({"event_type": "git_commit", "agent": "git", "commit": commit})

    assert event["commit"] == commit


def test_normalize_event_accepts_session_summary():
    event = normalize_event(
        {
            "event_type": "session_summary",
            "agent": "codex",
            "session_id": "session-1",
            "semantic": {
                "summary": "Implemented session summary logging",
                "outcome": "completed",
                "task_id": "TASK-8",
            },
        }
    )

    assert event["event_type"] == "session_summary"
    assert event["semantic"]["summary"] == "Implemented session summary logging"
    assert event["semantic"]["outcome"] == "completed"


def test_normalize_event_accepts_valid_iso_ts():
    event = normalize_event(
        {"event_type": "agent_start", "agent": "codex", "ts": "2026-05-31T10:00:00+03:00"}
    )

    assert event["ts"] == "2026-05-31T10:00:00+03:00"


def test_normalize_event_rejects_malformed_ts():
    with pytest.raises(ValueError, match="Invalid ts"):
        normalize_event({"event_type": "agent_start", "agent": "codex", "ts": "../../etc/passwd"})


def test_normalize_event_caps_long_free_text():
    long_note = "x" * (MAX_SEMANTIC_TEXT + 500)

    event = normalize_event(
        {"event_type": "semantic_note", "agent": "claude", "semantic": {"note": long_note}}
    )

    assert event["semantic"]["note"].endswith("…[truncated]")
    assert len(event["semantic"]["note"]) <= MAX_SEMANTIC_TEXT + len("…[truncated]")
