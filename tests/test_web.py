import json
import http.client
import threading
from datetime import date
from http.server import ThreadingHTTPServer

from agent_journal.events import normalize_event
from agent_journal.storage import write_event
from agent_journal.web import build_events_payload, create_web_handler, render_dashboard_html


def _event(event_type, ts="2026-06-01T10:00:00+03:00", **updates):
    raw = {"event_type": event_type, "agent": "claude", "ts": ts}
    raw.update(updates)
    return normalize_event(raw)


def test_build_events_payload_returns_summary_and_latest_events(tmp_path):
    write_event(
        tmp_path,
        _event("agent_start", session_id="summary-1", agent="codex", repo="/repo", branch="main", commit="abc123"),
    )
    write_event(
        tmp_path,
        _event(
            "session_summary",
            ts="2026-06-01T10:00:30+03:00",
            session_id="summary-1",
            agent="codex",
            repo="/repo",
            branch="main",
            commit="abc123",
            semantic={
                "task_id": "TASK-8",
                "summary": "Implemented session summary logging",
                "outcome": "completed",
            },
        ),
    )
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
    assert payload["raw_event_count"] == 4
    assert payload["summary"]["session_summaries"] == 1
    assert payload["summary"]["in_progress"] == 0
    assert payload["summary"]["notes"] == 1
    assert payload["summary"]["risky"] == 1
    assert payload["provider_coverage"]["codex"]["coverage_percent"] == 100
    assert payload["provider_coverage"]["claude"]["missing"] == 1
    assert payload["latest_events"][0]["event_type"] == "verification"
    assert payload["latest_events"][1]["event_type"] == "session_summary"
    session = next(item for item in payload["sessions"] if item["session_id"] == "summary-1")
    assert session["summary"] == "Implemented session summary logging"
    assert session["outcome"] == "completed"
    assert session["missing_summary"] is False
    json.dumps(payload)


def test_build_events_payload_marks_started_session_missing_summary(tmp_path):
    write_event(tmp_path, _event("agent_start", session_id="missing-1", agent="gemini", repo="/repo"))

    payload = build_events_payload(tmp_path, "2026-06-01")

    assert payload["sessions"][0]["session_id"] == "missing-1"
    assert payload["sessions"][0]["summary"] == "Missing semantic summary"
    assert "Wrapper captured start/end" in payload["sessions"][0]["diagnosis"]
    assert payload["sessions"][0]["missing_summary"] is True


def test_render_dashboard_html_contains_live_dashboard_controls():
    html = render_dashboard_html(default_date=date(2026, 6, 1), refresh_ms=2000)

    assert "Agent Journal Live" in html
    assert "/api/events" in html
    assert "X-Agent-Journal-Token" in html
    assert "setInterval" in html
    assert "Session Summaries" in html
    assert "Provider Coverage" in html
    assert "Likely cause" in html
    assert "data-section=\"sessions\"" in html
    assert "data-section=\"notes\"" in html
    assert "data-section=\"risky\"" in html
    assert "2026-06-01" in html


def test_web_handler_without_explicit_date_uses_current_day_per_request(tmp_path, monkeypatch):
    current = {"date": "2026-06-02"}
    monkeypatch.setattr("agent_journal.web._today_iso", lambda: current["date"])
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_web_handler(tmp_path, None))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    conn = http.client.HTTPConnection(host, port, timeout=5)

    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        html = response.read().decode("utf-8")
        assert response.status == 200
        assert 'value="2026-06-02"' in html

        current["date"] = "2026-06-03"
        conn.request("GET", "/api/events")
        response = conn.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert payload["date"] == "2026-06-03"
    finally:
        conn.close()
        server.shutdown()
        server.server_close()


def test_web_handler_with_explicit_date_keeps_that_date(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_journal.web._today_iso", lambda: "2026-06-02")
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_web_handler(tmp_path, "2026-06-01"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    conn = http.client.HTTPConnection(host, port, timeout=5)

    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        html = response.read().decode("utf-8")
        assert response.status == 200
        assert 'value="2026-06-01"' in html

        conn.request("GET", "/api/events")
        response = conn.getresponse()
        payload = json.loads(response.read())
        assert response.status == 200
        assert payload["date"] == "2026-06-01"
    finally:
        conn.close()
        server.shutdown()
        server.server_close()


def test_api_events_requires_token_when_configured(tmp_path):
    write_event(tmp_path, _event("semantic_note", semantic={"note": "private"}))
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        create_web_handler(tmp_path, "2026-06-01", api_token="secret"),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    conn = http.client.HTTPConnection(host, port, timeout=5)

    try:
        conn.request("GET", "/api/events?date=2026-06-01")
        response = conn.getresponse()
        body = response.read()
        assert response.status == 401
        assert b"unauthorized" in body

        conn.request("GET", "/api/events?date=2026-06-01", headers={"X-Agent-Journal-Token": "secret"})
        response = conn.getresponse()
        body = response.read()
        assert response.status == 200
        assert json.loads(body)["raw_event_count"] == 1
    finally:
        conn.close()
        server.shutdown()
        server.server_close()
