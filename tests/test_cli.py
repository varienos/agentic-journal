import json
import os
import subprocess
import sys
from pathlib import Path

from agent_journal.cli import main


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


def test_wrapper_preserves_exit_code_and_logs_events(tmp_path):
    wrapper = Path("scripts/wrappers/agent-journal-wrapper.sh").resolve()
    fake_bin = tmp_path / "fake-agent"
    fake_bin.write_text("#!/usr/bin/env sh\nexit 7\n")
    fake_bin.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_JOURNAL_HOME"] = str(tmp_path / "journal")
    env["AGENT_JOURNAL_AGENT"] = "codex"
    env["AGENT_JOURNAL_REAL_BIN"] = str(fake_bin)

    result = subprocess.run([str(wrapper)], env=env, check=False)

    assert result.returncode == 7
    event_file = next((tmp_path / "journal" / "events").glob("*.jsonl"))
    event_types = [json.loads(line)["event_type"] for line in event_file.read_text().splitlines()]
    assert event_types == ["agent_start", "agent_end"]
