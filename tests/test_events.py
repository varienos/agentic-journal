from agent_journal.events import normalize_event


def test_normalize_event_adds_required_fields():
    event = normalize_event({"event_type": "agent_start", "agent": "codex"})

    assert event["schema_version"] == 1
    assert event["event_id"]
    assert event["ts"]
    assert event["event_type"] == "agent_start"
    assert event["agent"] == "codex"
    assert event["semantic"] == {}
    assert event["evidence"] == {}


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

