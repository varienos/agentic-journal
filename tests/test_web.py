import json
from datetime import date

from agent_journal.events import normalize_event
from agent_journal.storage import write_event
from agent_journal.web import build_events_payload, render_dashboard_html


def _event(event_type, ts="2026-06-01T10:00:00+03:00", **updates):
    raw = {"event_type": event_type, "agent": "claude", "ts": ts}
    raw.update(updates)
    return normalize_event(raw)


def test_build_events_payload_returns_summary_and_latest_events(tmp_path):
    write_event(
        tmp_path,
        _event("semantic_note", semantic={"note": "Claude MCP bağlantısı test edildi"}),
    )
    write_event(
        tmp_path,
        _event(
            "verification",
            ts="2026-06-01T10:01:00+03:00",
            session_id="missing-1",
            semantic={"status": "journal_missing", "note": "Session ended without semantic journal entry"},
            evidence={"verification_status": "failed", "verification": "agent-journal guard session-end"},
        ),
    )

    payload = build_events_payload(tmp_path, "2026-06-01")

    assert payload["date"] == "2026-06-01"
    assert payload["raw_event_count"] == 2
    assert payload["summary"]["notes"] == 1
    assert payload["summary"]["risky"] == 1
    assert payload["latest_events"][0]["event_type"] == "verification"
    assert payload["latest_events"][1]["event_type"] == "semantic_note"
    json.dumps(payload)


def test_render_dashboard_html_contains_live_dashboard_controls():
    html = render_dashboard_html(default_date=date(2026, 6, 1), refresh_ms=2000)

    assert "Agent Journal Live" in html
    assert "/api/events" in html
    assert "setInterval" in html
    assert "data-section=\"notes\"" in html
    assert "data-section=\"risky\"" in html
    assert "2026-06-01" in html
