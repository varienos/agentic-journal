from agent_journal.mcp_server import (
    create_mcp_server,
    journal_note,
    journal_session_summary,
    journal_task_blocked,
    journal_task_completed,
)
from agent_journal.storage import read_events_for_date


def test_journal_note_writes_semantic_note(tmp_path):
    result = journal_note(journal_home=tmp_path, agent="codex", note="Investigated TASK-1")

    assert result == "logged"
    events = read_events_for_date(tmp_path, None)
    assert events[0]["event_type"] == "semantic_note"
    assert events[0]["semantic"]["note"] == "Investigated TASK-1"


def test_journal_task_completed_writes_claim(tmp_path):
    result = journal_task_completed(journal_home=tmp_path, agent="claude", task_id="TASK-2", note="Done")

    assert result == "logged"
    events = read_events_for_date(tmp_path, None)
    assert events[0]["event_type"] == "task_completed_claim"
    assert events[0]["semantic"]["task_id"] == "TASK-2"


def test_journal_task_blocked_writes_blocked_event(tmp_path):
    result = journal_task_blocked(journal_home=tmp_path, agent="gemini", task_id="TASK-3", reason="Missing key")

    assert result == "logged"
    events = read_events_for_date(tmp_path, None)
    assert events[0]["event_type"] == "task_blocked"
    assert events[0]["semantic"]["status"] == "blocked"


def test_journal_session_summary_writes_outcome_event(tmp_path):
    result = journal_session_summary(
        journal_home=tmp_path,
        agent="codex",
        session_id="session-1",
        task_id="TASK-8",
        summary="Implemented session summary logging",
        outcome="completed",
    )

    assert result == "logged"
    events = read_events_for_date(tmp_path, None)
    assert events[0]["event_type"] == "session_summary"
    assert events[0]["session_id"] == "session-1"
    assert events[0]["semantic"]["task_id"] == "TASK-8"
    assert events[0]["semantic"]["summary"] == "Implemented session summary logging"
    assert events[0]["semantic"]["outcome"] == "completed"


def test_create_mcp_server_has_expected_name_or_clear_dependency_error():
    try:
        server = create_mcp_server()
    except RuntimeError as exc:
        assert "mcp" in str(exc).lower()
    else:
        assert getattr(server, "name", None) == "agent-journal"


def test_create_mcp_server_registers_expected_tool_names():
    try:
        server = create_mcp_server()
    except RuntimeError:
        return

    assert {
        "journal_note",
        "journal_session_summary",
        "journal_task_completed",
        "journal_task_blocked",
        "journal_daily_report",
    }.issubset(set(server._tool_manager._tools))
