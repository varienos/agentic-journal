import os
from pathlib import Path
import subprocess

from agentic_journal.diagnostics import build_doctor_report, build_doctor_result
from agentic_journal.events import normalize_event
from agentic_journal.storage import write_event


def _event(event_type, **updates):
    raw = {"event_type": event_type, "agent": "codex", "ts": "2026-06-02T10:00:00+03:00"}
    raw.update(updates)
    return normalize_event(raw)


def _executable(path: Path) -> None:
    path.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def test_doctor_reports_wrappers_instructions_hook_counts_and_web_token(tmp_path):
    journal = tmp_path / "journal"
    wrapper_bin = journal / "bin"
    wrapper_bin.mkdir(parents=True)
    for agent in ("codex", "claude", "gemini"):
        _executable(wrapper_bin / agent)

    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".claude").mkdir(parents=True)
    (home / ".gemini").mkdir(parents=True)
    (home / ".codex" / "AGENTS.md").write_text("journal_session_summary\n", encoding="utf-8")
    (home / ".claude" / "CLAUDE.md").write_text("journal_session_summary\n", encoding="utf-8")
    (home / ".gemini" / "GEMINI.md").write_text("journal_session_summary\n", encoding="utf-8")
    (home / ".codex" / "config.toml").write_text("agentic-journal-mcp\n", encoding="utf-8")
    (home / ".claude.json").write_text('{"agentic-journal": {"command": "agentic-journal-mcp"}}\n', encoding="utf-8")
    (home / ".gemini" / "settings.json").write_text("agentic-journal-mcp\n", encoding="utf-8")

    repo = tmp_path / "repo"
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True)
    hook = hooks / "post-commit"
    hook.write_text("agentic-journal event --type git_commit\n", encoding="utf-8")
    hook.chmod(0o755)

    write_event(journal, _event("agent_start", agent="codex", session_id="codex-1"))
    write_event(journal, _event("session_summary", agent="codex", session_id="codex-1"))
    write_event(journal, _event("agent_start", agent="gemini", session_id="gemini-1"))
    write_event(
        journal,
        _event(
            "verification",
            agent="gemini",
            session_id="gemini-1",
            semantic={"status": "journal_missing"},
            evidence={"verification_status": "failed"},
        ),
    )

    result = build_doctor_result(
        journal,
        "2026-06-02",
        home=home,
        cwd=repo,
        path_env=f"{wrapper_bin}{os.pathsep}/usr/bin",
        web_token="secret",
    )

    assert result["wrappers"]["codex"]["status"] == "ok"
    assert result["instructions"]["claude"]["status"] == "ok"
    assert result["mcp"]["gemini"]["status"] == "configured"
    assert result["git_hook"]["status"] == "ok"
    assert result["web"]["status"] == "token_configured"
    assert result["events"]["session_summaries"] == 1
    assert result["events"]["journal_missing"] == 1
    assert result["provider_coverage"]["codex"]["coverage_percent"] == 100
    assert result["provider_coverage"]["gemini"]["missing"] == 1


def test_doctor_report_is_human_readable(tmp_path):
    result = {
        "date": "2026-06-02",
        "wrappers": {"codex": {"status": "missing", "path": None}},
        "mcp": {"codex": {"status": "missing", "path": None}},
        "instructions": {"codex": {"status": "missing", "path": None}},
        "git_hook": {"status": "missing", "path": None},
        "web": {"status": "local_default", "token_required": False},
        "events": {"raw": 0, "session_summaries": 0, "journal_missing": 0},
        "provider_coverage": {
            "codex": {
                "sessions": 0,
                "summarized": 0,
                "missing": 0,
                "in_progress": 0,
                "coverage_percent": 0,
            }
        },
    }

    report = build_doctor_report(result)

    assert "# Agentic Journal Doctor" in report
    assert "codex wrapper: missing" in report
    assert "Session summaries: 0" in report
    assert "codex: 0 sessions, 0 summarized, 0 missing, 0 in progress, 0% coverage" in report


def test_doctor_detects_gemini_project_mcp_hint_from_projects_json(tmp_path):
    journal = tmp_path / "journal"
    home = tmp_path / "home"
    (home / ".gemini").mkdir(parents=True)
    (home / ".gemini" / "projects.json").write_text(
        '{"projects": {"/repo": "agentic-journal"}}',
        encoding="utf-8",
    )

    result = build_doctor_result(journal, "2026-06-02", home=home, cwd=tmp_path)

    assert result["mcp"]["gemini"]["status"] == "configured"
    assert result["mcp"]["gemini"]["path"].endswith("projects.json")


def test_doctor_detects_git_hook_from_worktree_checkout(tmp_path):
    repo = tmp_path / "repo"
    worktree = tmp_path / "worktree"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "worktree", "add", str(worktree)], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    hook = repo / ".git" / "hooks" / "post-commit"
    hook.write_text("agentic-journal event --type git_commit\n", encoding="utf-8")
    hook.chmod(0o755)

    result = build_doctor_result(tmp_path / "journal", "2026-06-02", cwd=worktree)

    assert result["git_hook"]["status"] == "ok"
    assert result["git_hook"]["path"] == str(hook)
