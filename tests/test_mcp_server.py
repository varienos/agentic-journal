import subprocess

import agentic_journal.mcp_server as mcp_server
from agentic_journal.mcp_server import (
    create_mcp_server,
    journal_note,
    journal_session_summary,
    journal_task_blocked,
    journal_task_completed,
)
from agentic_journal.storage import read_events_for_date


def _init_git_repo(path):
    path.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "tracked.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "add tracked"], cwd=path, check=True, stdout=subprocess.DEVNULL)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()


def test_journal_note_writes_semantic_note(tmp_path):
    result = journal_note(journal_home=tmp_path, agent="codex", note="Investigated TASK-1")

    assert result == "logged"
    events = read_events_for_date(tmp_path, None)
    assert events[0]["event_type"] == "semantic_note"
    assert events[0]["semantic"]["note"] == "Investigated TASK-1"


def test_journal_note_skips_blank_note(tmp_path):
    result = journal_note(journal_home=tmp_path, agent="codex", note="   ")

    assert result == "skipped: note is required"
    assert read_events_for_date(tmp_path, None) == []


def test_journal_task_completed_writes_claim(tmp_path):
    result = journal_task_completed(journal_home=tmp_path, agent="claude", task_id="TASK-2", note="Done")

    assert result == "logged"
    events = read_events_for_date(tmp_path, None)
    assert events[0]["event_type"] == "task_completed_claim"
    assert events[0]["semantic"]["task_id"] == "TASK-2"


def test_journal_task_completed_skips_without_task_or_note(tmp_path):
    result = journal_task_completed(journal_home=tmp_path, agent="claude", task_id="", note="  ")

    assert result == "skipped: task_id or note is required"
    assert read_events_for_date(tmp_path, None) == []


def test_journal_task_blocked_writes_blocked_event(tmp_path):
    result = journal_task_blocked(journal_home=tmp_path, agent="gemini", task_id="TASK-3", reason="Missing key")

    assert result == "logged"
    events = read_events_for_date(tmp_path, None)
    assert events[0]["event_type"] == "task_blocked"
    assert events[0]["semantic"]["status"] == "blocked"


def test_journal_task_blocked_skips_blank_reason(tmp_path):
    result = journal_task_blocked(journal_home=tmp_path, agent="gemini", task_id="TASK-3", reason=" ")

    assert result == "skipped: reason is required"
    assert read_events_for_date(tmp_path, None) == []


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


def test_journal_session_summary_skips_blank_summary(tmp_path):
    result = journal_session_summary(
        journal_home=tmp_path,
        agent="codex",
        session_id="session-1",
        summary=" ",
        outcome="completed",
    )

    assert result == "skipped: summary is required"
    assert read_events_for_date(tmp_path, None) == []


def test_journal_model_operation_writes_activity_event(tmp_path):
    result = mcp_server.journal_model_operation(
        journal_home=tmp_path,
        agent="cortex",
        session_id="chat-1",
        provider="claude",
        model="claude-opus-4-8-thinking-high",
        operation="chat",
        source="/api/chat",
        status="completed",
        duration_ms=1234,
        input_tokens=1200,
        output_tokens=340,
        cached_input_tokens=100,
        reasoning_tokens=50,
        error_code="rate_limit",
    )

    assert result == "logged"
    event = read_events_for_date(tmp_path, None)[0]
    assert event["event_type"] == "model_operation"
    assert event["semantic"] == {
        "provider": "claude",
        "model": "claude-opus-4-8-thinking-high",
        "operation": "chat",
        "source": "/api/chat",
        "status": "completed",
    }
    assert event["evidence"]["token_usage"]["input_tokens"] == 1200
    assert event["evidence"]["error_code"] == "rate_limit"


def test_journal_model_operation_skips_without_metadata(tmp_path):
    result = mcp_server.journal_model_operation(journal_home=tmp_path, agent="cortex")

    assert result == "skipped: model operation metadata is required"
    assert read_events_for_date(tmp_path, None) == []


def test_mcp_tools_attach_session_and_git_context(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    head = _init_git_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTIC_JOURNAL_SESSION_ID", "session-env")

    journal_note(journal_home=tmp_path / "journal", agent="codex", note="Investigated")
    journal_task_completed(journal_home=tmp_path / "journal", agent="claude", task_id="TASK-2", note="Done")
    journal_task_blocked(journal_home=tmp_path / "journal", agent="gemini", task_id="TASK-3", reason="Missing key")
    journal_session_summary(
        journal_home=tmp_path / "journal",
        agent="codex",
        task_id="TASK-8",
        summary="Implemented session summary logging",
        outcome="completed",
    )
    mcp_server.journal_model_operation(
        journal_home=tmp_path / "journal",
        agent="cortex",
        provider="claude",
        model="claude-opus-4-8-thinking-high",
        operation="chat",
        status="completed",
    )

    events = read_events_for_date(tmp_path / "journal", None)
    assert [event["session_id"] for event in events] == ["session-env"] * 5
    assert {event["repo"] for event in events} == {str(repo)}
    assert {event["branch"] for event in events} == {"main"}
    assert {event["commit"] for event in events} == {head}
    assert {event["cwd"] for event in events} == {str(repo)}


def test_mcp_tools_accept_legacy_session_env(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENTIC_JOURNAL_SESSION_ID", raising=False)
    monkeypatch.setenv("AGENT_JOURNAL_SESSION_ID", "legacy-session")

    journal_note(journal_home=tmp_path, agent="codex", note="legacy session")

    event = read_events_for_date(tmp_path, None)[0]
    assert event["session_id"] == "legacy-session"


def test_create_mcp_server_has_expected_name_or_clear_dependency_error():
    try:
        server = create_mcp_server()
    except RuntimeError as exc:
        assert "mcp" in str(exc).lower()
    else:
        assert getattr(server, "name", None) == "agentic-journal"


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
        "journal_model_operation",
        "journal_daily_report",
    }.issubset(set(server._tool_manager._tools))
