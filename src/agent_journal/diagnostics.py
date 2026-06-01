from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agent_journal.git_hooks import resolve_git_hook_path
from agent_journal.report import DEFAULT_PROVIDERS, build_provider_coverage
from agent_journal.storage import read_events_for_date


def _which(command: str, path_env: str | None = None) -> Path | None:
    for entry in (path_env or os.environ.get("PATH", "")).split(os.pathsep):
        directory = Path(entry or ".").expanduser()
        candidate = directory / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _contains(path: Path, needles: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return all(needle in text for needle in needles)


def _wrapper_status(root: Path, path_env: str | None) -> dict[str, dict[str, str | None]]:
    wrapper_dir = (root / "bin").resolve()
    results = {}
    for agent in DEFAULT_PROVIDERS:
        found = _which(agent, path_env)
        if not found:
            results[agent] = {"status": "missing", "path": None}
            continue
        status = "ok" if found.resolve().is_relative_to(wrapper_dir) else "bypassed"
        results[agent] = {"status": status, "path": str(found)}
    return results


def _instruction_status(home: Path) -> dict[str, dict[str, str | None]]:
    paths = {
        "codex": home / ".codex" / "AGENTS.md",
        "claude": home / ".claude" / "CLAUDE.md",
        "gemini": home / ".gemini" / "GEMINI.md",
    }
    results = {}
    for agent, path in paths.items():
        results[agent] = {
            "status": "ok" if _contains(path, ("journal_session_summary",)) else "missing",
            "path": str(path),
        }
    return results


def _mcp_status(home: Path) -> dict[str, dict[str, str | None]]:
    paths = {
        "codex": home / ".codex" / "config.toml",
        "claude": home / ".claude.json",
        "gemini": home / ".gemini" / "settings.json",
    }
    results = {}
    for agent, path in paths.items():
        configured = _contains(path, ("agent-journal",)) or _contains(path, ("agent_journal",))
        if agent == "gemini" and not configured:
            project_path = home / ".gemini" / "projects.json"
            if _contains(project_path, ("agent-journal",)):
                results[agent] = {"status": "configured", "path": str(project_path)}
                continue
        results[agent] = {"status": "configured" if configured else "missing", "path": str(path)}
    return results


def _git_hook_status(cwd: Path) -> dict[str, str | None]:
    hook = resolve_git_hook_path(cwd)
    if hook.exists():
        if _contains(hook, ("agent-journal",)) and os.access(hook, os.X_OK):
            return {"status": "ok", "path": str(hook)}
        if _contains(hook, ("agent-journal",)):
            return {"status": "not_executable", "path": str(hook)}
        return {"status": "missing", "path": str(hook)}
    return {"status": "missing", "path": str(hook) if _inside_git_worktree(cwd) else None}


def _inside_git_worktree(cwd: Path) -> bool:
    git_file_or_dir = cwd / ".git"
    return git_file_or_dir.exists()


def _event_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "raw": len(events),
        "session_summaries": sum(1 for event in events if event.get("event_type") == "session_summary"),
        "journal_missing": sum(
            1
            for event in events
            if event.get("event_type") == "verification"
            and (event.get("semantic") or {}).get("status") == "journal_missing"
        ),
    }


def build_doctor_result(
    root: str | Path,
    report_date: str,
    *,
    home: str | Path | None = None,
    cwd: str | Path | None = None,
    path_env: str | None = None,
    web_token: str | None = None,
) -> dict[str, Any]:
    root_path = Path(root).expanduser()
    home_path = Path(home).expanduser() if home else Path.home()
    cwd_path = Path(cwd).expanduser() if cwd else Path.cwd()
    events = read_events_for_date(root_path, report_date)
    token = web_token if web_token is not None else os.environ.get("AGENT_JOURNAL_WEB_TOKEN")
    return {
        "date": report_date,
        "wrappers": _wrapper_status(root_path, path_env),
        "mcp": _mcp_status(home_path),
        "instructions": _instruction_status(home_path),
        "git_hook": _git_hook_status(cwd_path),
        "web": {
            "status": "token_configured" if token else "local_default",
            "token_required": bool(token),
        },
        "events": _event_counts(events),
        "provider_coverage": build_provider_coverage(events),
    }


def build_doctor_report(result: dict[str, Any]) -> str:
    lines = [
        "# Agent Journal Doctor",
        f"Date: {result['date']}",
        "",
        "## Wrapper PATH",
    ]
    for agent, status in sorted(result["wrappers"].items()):
        path = f" ({status['path']})" if status.get("path") else ""
        lines.append(f"- {agent} wrapper: {status['status']}{path}")

    lines.append("")
    lines.append("## MCP Config Hints")
    for agent, status in sorted(result["mcp"].items()):
        path = f" ({status['path']})" if status.get("path") else ""
        lines.append(f"- {agent} MCP: {status['status']}{path}")

    lines.append("")
    lines.append("## Global Instructions")
    for agent, status in sorted(result["instructions"].items()):
        path = f" ({status['path']})" if status.get("path") else ""
        lines.append(f"- {agent} instructions: {status['status']}{path}")

    lines.extend(
        [
            "",
            "## Journal Events",
            f"- Raw events: {result['events']['raw']}",
            f"- Session summaries: {result['events']['session_summaries']}",
            f"- journal_missing: {result['events']['journal_missing']}",
            "",
            "## Provider Coverage",
        ]
    )
    for agent, stats in sorted(result["provider_coverage"].items()):
        lines.append(
            "- "
            f"{agent}: {stats['sessions']} sessions, "
            f"{stats['summarized']} summarized, "
            f"{stats['missing']} missing, "
            f"{stats['in_progress']} in progress, "
            f"{stats['coverage_percent']}% coverage"
        )

    hook = result["git_hook"]
    hook_path = f" ({hook['path']})" if hook.get("path") else ""
    lines.extend(
        [
            "",
            "## Git Hook",
            f"- post-commit: {hook['status']}{hook_path}",
            "",
            "## Dashboard/API Token",
            f"- status: {result['web']['status']}",
        ]
    )
    return "\n".join(lines) + "\n"
