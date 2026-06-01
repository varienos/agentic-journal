import json
import os
import subprocess
import sys
from pathlib import Path

from agent_journal.cli import main
from agent_journal.install import generate_wrapper_script


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


def test_web_help_exits_cleanly(capsys):
    exit_code = main(["web", "--help"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "--host" in output
    assert "--port" in output
    assert "--date" in output


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
