import json
import os
import subprocess
import sys
from pathlib import Path

from agent_journal.cli import main
from agent_journal.install import generate_wrapper_script
from agent_journal.mcp_server import journal_task_blocked, journal_task_completed


def test_main_help_exits_cleanly(capsys):
    exit_code = main(["--help"])

    assert exit_code == 0
    assert "agent-journal" in capsys.readouterr().out


def test_event_command_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))

    exit_code = main(["event", "--type", "agent_start", "--agent", "codex"])

    assert exit_code == 0
    event_file = tmp_path / "events" / "2026-05-31.jsonl"
    if not event_file.exists():
        event_file = next((tmp_path / "events").glob("*.jsonl"))
    event = json.loads(event_file.read_text().splitlines()[0])
    assert event["event_type"] == "agent_start"
    assert event["agent"] == "codex"
    assert (tmp_path / "config.toml").exists()


def test_event_command_accepts_semantic_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))

    exit_code = main(
        [
            "event",
            "--type",
            "task_completed_claim",
            "--agent",
            "gemini",
            "--task",
            "TASK-1",
            "--note",
            "Smoke test completed",
        ]
    )

    assert exit_code == 0
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    event = json.loads(event_file.read_text().splitlines()[0])
    assert event["semantic"]["task_id"] == "TASK-1"
    assert event["semantic"]["note"] == "Smoke test completed"


def test_event_command_writes_session_summary_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))

    exit_code = main(
        [
            "event",
            "--type",
            "session_summary",
            "--agent",
            "codex",
            "--session-id",
            "session-1",
            "--task",
            "TASK-8",
            "--summary",
            "Implemented session summary logging",
            "--outcome",
            "completed",
        ]
    )

    assert exit_code == 0
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    event = json.loads(event_file.read_text().splitlines()[0])
    assert event["event_type"] == "session_summary"
    assert event["session_id"] == "session-1"
    assert event["semantic"]["task_id"] == "TASK-8"
    assert event["semantic"]["summary"] == "Implemented session summary logging"
    assert event["semantic"]["outcome"] == "completed"


def test_report_command_writes_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    main(["event", "--type", "task_completed_claim", "--agent", "codex", "--task", "TASK-1"])

    exit_code = main(["report", "--date", "2026-05-31"])

    assert exit_code == 0
    report_files = list((tmp_path / "reports").glob("*.md"))
    assert report_files
    assert "Completed Claimed" in report_files[0].read_text()


def test_report_command_accepts_explicit_write_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))

    exit_code = main(["report", "--date", "2026-05-31", "--write"])

    assert exit_code == 0
    assert (tmp_path / "reports" / "2026-05-31.md").exists()


def test_status_command_prints_today_summary(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    main(["event", "--type", "agent_start", "--agent", "codex"])

    exit_code = main(["status", "--date", "2026-05-31"])

    assert exit_code == 0
    assert "Raw events:" in capsys.readouterr().out


def test_doctor_command_prints_setup_and_coverage(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    main(["event", "--type", "agent_start", "--agent", "codex", "--session-id", "doctor-1"])
    main(
        [
            "event",
            "--type",
            "session_summary",
            "--agent",
            "codex",
            "--session-id",
            "doctor-1",
            "--summary",
            "Doctor smoke",
            "--outcome",
            "completed",
        ]
    )

    exit_code = main(["doctor", "--date", "2026-05-31"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Agent Journal Doctor" in output
    assert "Session summaries:" in output
    assert "codex:" in output


def test_web_help_exits_cleanly(capsys):
    exit_code = main(["web", "--help"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "--host" in output
    assert "--port" in output
    assert "--date" in output
    assert "--token" in output


def test_web_command_without_explicit_date_uses_dynamic_default(monkeypatch):
    calls = {}

    def fake_run_web_server(root, host, port, default_date, refresh_ms=2000, api_token=None):
        calls["default_date"] = default_date
        calls["refresh_ms"] = refresh_ms

    monkeypatch.setattr("agent_journal.cli.run_web_server", fake_run_web_server)

    exit_code = main(["web", "--today", "--refresh-ms", "3000"])

    assert exit_code == 0
    assert calls["default_date"] is None
    assert calls["refresh_ms"] == 3000


def test_web_command_with_explicit_date_keeps_that_date(monkeypatch):
    calls = {}

    def fake_run_web_server(root, host, port, default_date, refresh_ms=2000, api_token=None):
        calls["default_date"] = default_date

    monkeypatch.setattr("agent_journal.cli.run_web_server", fake_run_web_server)

    exit_code = main(["web", "--date", "2026-06-01"])

    assert exit_code == 0
    assert calls["default_date"] == "2026-06-01"


def test_guard_session_end_writes_risky_fallback_when_semantic_entry_is_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    main(["event", "--type", "agent_start", "--agent", "claude", "--session-id", "session-1"])
    main(["event", "--type", "agent_end", "--agent", "claude", "--session-id", "session-1"])

    exit_code = main(["guard", "session-end", "--agent", "claude", "--session-id", "session-1"])
    second_exit_code = main(["guard", "session-end", "--agent", "claude", "--session-id", "session-1"])

    assert exit_code == 0
    assert second_exit_code == 0
    assert "guarded" in capsys.readouterr().out
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    events = [json.loads(line) for line in event_file.read_text().splitlines()]
    guard_events = [event for event in events if event["event_type"] == "verification"]
    assert len(guard_events) == 1
    assert guard_events[0]["evidence"]["verification_status"] == "failed"
    assert guard_events[0]["semantic"]["status"] == "journal_missing"


def test_guard_session_end_skips_when_semantic_entry_exists(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    main(["event", "--type", "agent_start", "--agent", "claude", "--session-id", "session-2"])
    main(
        [
            "event",
            "--type",
            "task_completed_claim",
            "--agent",
            "claude",
            "--session-id",
            "session-2",
            "--task",
            "TASK-5",
        ]
    )

    exit_code = main(["guard", "session-end", "--agent", "claude", "--session-id", "session-2"])

    assert exit_code == 0
    assert "semantic journal entry exists" in capsys.readouterr().out
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    events = [json.loads(line) for line in event_file.read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["agent_start", "task_completed_claim"]


def test_guard_session_end_requires_session_outcome_not_generic_note(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    main(["event", "--type", "agent_start", "--agent", "claude", "--session-id", "session-3"])
    main(["event", "--type", "semantic_note", "--agent", "claude", "--session-id", "session-3", "--note", "FYI"])

    exit_code = main(["guard", "session-end", "--agent", "claude", "--session-id", "session-3"])

    assert exit_code == 0
    assert "guarded" in capsys.readouterr().out
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    events = [json.loads(line) for line in event_file.read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["agent_start", "semantic_note", "verification"]


def test_guard_session_end_records_changed_files_as_objective_fallback_context(tmp_path, monkeypatch):
    journal = tmp_path / "journal"
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add tracked"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    (repo / "tracked.txt").write_text("after\n", encoding="utf-8")
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(journal))
    monkeypatch.chdir(repo)
    main(["event", "--type", "agent_start", "--agent", "claude", "--session-id", "session-files"])

    exit_code = main(["guard", "session-end", "--agent", "claude", "--session-id", "session-files"])

    assert exit_code == 0
    event_file = next((journal / "events").glob("*.jsonl"))
    events = [json.loads(line) for line in event_file.read_text().splitlines()]
    fallback = [event for event in events if event["event_type"] == "verification"][-1]
    assert fallback["files_changed"] == ["tracked.txt"]


def test_guard_session_end_skips_when_session_summary_exists(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    main(["event", "--type", "agent_start", "--agent", "claude", "--session-id", "session-4"])
    main(
        [
            "event",
            "--type",
            "session_summary",
            "--agent",
            "claude",
            "--session-id",
            "session-4",
            "--summary",
            "Reviewed MCP setup",
            "--outcome",
            "completed",
        ]
    )

    exit_code = main(["guard", "session-end", "--agent", "claude", "--session-id", "session-4"])

    assert exit_code == 0
    assert "semantic journal entry exists" in capsys.readouterr().out
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    events = [json.loads(line) for line in event_file.read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["agent_start", "session_summary"]


def test_guard_session_end_skips_when_mcp_task_completed_uses_session_env(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    monkeypatch.setenv("AGENT_JOURNAL_SESSION_ID", "session-5")
    main(["event", "--type", "agent_start", "--agent", "claude", "--session-id", "session-5"])
    journal_task_completed(agent="claude", task_id="TASK-5", note="Done")

    exit_code = main(["guard", "session-end", "--agent", "claude", "--session-id", "session-5"])

    assert exit_code == 0
    assert "semantic journal entry exists" in capsys.readouterr().out
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    events = [json.loads(line) for line in event_file.read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["agent_start", "task_completed_claim"]


def test_guard_session_end_skips_when_mcp_task_blocked_uses_session_env(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    monkeypatch.setenv("AGENT_JOURNAL_SESSION_ID", "session-6")
    main(["event", "--type", "agent_start", "--agent", "gemini", "--session-id", "session-6"])
    journal_task_blocked(agent="gemini", task_id="TASK-6", reason="Missing key")

    exit_code = main(["guard", "session-end", "--agent", "gemini", "--session-id", "session-6"])

    assert exit_code == 0
    assert "semantic journal entry exists" in capsys.readouterr().out
    event_file = next((tmp_path / "events").glob("*.jsonl"))
    events = [json.loads(line) for line in event_file.read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["agent_start", "task_blocked"]


def test_wrapper_preserves_exit_code_and_logs_events(tmp_path):
    fake_bin = tmp_path / "fake-agent"
    fake_bin.write_text("#!/usr/bin/env sh\nexit 7\n")
    fake_bin.chmod(0o755)
    wrapper = tmp_path / "codex"
    wrapper.write_text(generate_wrapper_script("codex", str(fake_bin)), encoding="utf-8")
    wrapper.chmod(0o755)
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    agent_journal = shim_dir / "agent-journal"
    agent_journal.write_text(
        f'#!/usr/bin/env sh\nPYTHONPATH="{Path("src").resolve()}" "{sys.executable}" -m agent_journal.cli "$@"\n',
        encoding="utf-8",
    )
    agent_journal.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_JOURNAL_HOME"] = str(tmp_path / "journal")
    env["PATH"] = f"{shim_dir}:{env['PATH']}"

    result = subprocess.run([str(wrapper)], env=env, check=False)

    assert result.returncode == 7
    event_file = next((tmp_path / "journal" / "events").glob("*.jsonl"))
    event_types = [json.loads(line)["event_type"] for line in event_file.read_text().splitlines()]
    assert event_types == ["agent_start", "agent_end", "verification"]


def test_git_commit_event_records_head_commit_and_committed_files(tmp_path, monkeypatch):
    journal = tmp_path / "journal"
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("hello\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add tracked"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(journal))
    monkeypatch.chdir(repo)

    exit_code = main(["event", "--type", "git_commit", "--agent", "git"])

    assert exit_code == 0
    event_file = next((journal / "events").glob("*.jsonl"))
    event = json.loads(event_file.read_text().splitlines()[0])
    assert event["commit"] == head
    assert event["files_changed"] == ["tracked.txt"]
