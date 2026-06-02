from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

from agent_journal.config import journal_root
from agent_journal.diagnostics import build_doctor_report, build_doctor_result
from agent_journal.events import normalize_event
from agent_journal.git_context import get_git_context, get_head_commit_files
from agent_journal.install import (
    claude_mcp_snippet,
    codex_mcp_snippet,
    gemini_mcp_snippet,
    install_agent_instructions,
    install_git_hook,
    install_shell_profile,
    install_wrappers,
)
from agent_journal.report import build_provider_coverage, classify_daily_work, render_markdown_report
from agent_journal.storage import read_events_for_date, write_event
from agent_journal.web import run_web_server

SESSION_OUTCOME_EVENT_TYPES = {"session_summary", "task_completed_claim", "task_blocked"}
JOURNAL_MISSING_STATUS = "journal_missing"


def _add_event_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("event", help="Write an event")
    parser.add_argument("--type", required=True, dest="event_type")
    parser.add_argument("--agent", required=True)
    parser.add_argument("--task")
    parser.add_argument("--note")
    parser.add_argument("--summary")
    parser.add_argument(
        "--outcome",
        choices=["completed", "in_progress", "blocked", "no_work", "unknown"],
    )
    parser.add_argument("--reason")
    parser.add_argument("--session-id")
    parser.add_argument("--command", dest="agent_command")
    parser.add_argument("--exit-code", type=int)
    parser.add_argument("--duration-ms", type=int)
    parser.add_argument("--verification")
    parser.add_argument("--verification-status", choices=["passed", "failed"])


def _add_report_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("report", help="Generate a daily report")
    parser.add_argument("--today", action="store_true")
    parser.add_argument("--date")
    parser.add_argument("--print", action="store_true", dest="print_report")
    parser.add_argument("--write", action="store_true", help="Write report to disk (default behavior)")
    parser.add_argument("--output")


def _add_status_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("status", help="Print a compact daily status")
    parser.add_argument("--today", action="store_true")
    parser.add_argument("--date")


def _add_doctor_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("doctor", help="Audit Agent Journal setup and daily coverage")
    parser.add_argument("--today", action="store_true")
    parser.add_argument("--date")


def _add_web_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("web", help="Run the live web dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--today", action="store_true")
    parser.add_argument("--date")
    parser.add_argument("--refresh-ms", type=int, default=2000)
    parser.add_argument("--token", help="Require this token for /api/events requests")


def _add_install_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("install", help="Install wrappers or print setup instructions")
    install_sub = parser.add_subparsers(dest="install_target")
    install_sub.add_parser("wrappers", help="Install codex/claude/gemini wrappers")
    install_sub.add_parser("shell-profile", help="Add wrapper PATH setup to .zprofile and .zshrc")
    install_sub.add_parser("agent-instructions", help="Add Agent Journal reporting rules to global agent instruction files")
    git_hook = install_sub.add_parser("git-hook", help="Install post-commit hook into a repo")
    git_hook.add_argument("--repo", default=".")
    install_sub.add_parser("mcp-snippets", help="Print MCP config snippets")


def _add_guard_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("guard", help="Enforce journal lifecycle expectations")
    guard_sub = parser.add_subparsers(dest="guard_target")
    session_end = guard_sub.add_parser("session-end", help="Write a fallback event if a session lacks semantic journal output")
    session_end.add_argument("--agent", required=True)
    session_end.add_argument("--session-id", required=True)
    session_end.add_argument(
        "--note",
        default="Session ended without semantic journal entry",
        help="Fallback note written when no semantic event exists for the session",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-journal")
    subparsers = parser.add_subparsers(dest="command")
    _add_event_parser(subparsers)
    _add_report_parser(subparsers)
    _add_status_parser(subparsers)
    _add_doctor_parser(subparsers)
    _add_web_parser(subparsers)
    _add_install_parser(subparsers)
    _add_guard_parser(subparsers)
    return parser


def _event_from_args(args: argparse.Namespace) -> dict:
    cwd = Path.cwd()
    git_context = get_git_context(cwd)
    semantic = {}
    if args.task:
        semantic["task_id"] = args.task
    if args.note:
        semantic["note"] = args.note
    if args.summary:
        semantic["summary"] = args.summary
    if args.outcome:
        semantic["outcome"] = args.outcome
    if args.reason:
        semantic["reason"] = args.reason
    if args.event_type == "task_completed_claim":
        semantic["status"] = "completed_claimed"
    if args.event_type == "task_blocked":
        semantic["status"] = "blocked"

    evidence = {}
    if args.verification:
        evidence["verification"] = args.verification
    if args.verification_status:
        evidence["verification_status"] = args.verification_status

    files_changed = git_context.get("changed_files") or []
    if args.event_type == "git_commit":
        files_changed = get_head_commit_files(cwd)

    return normalize_event(
        {
            "event_type": args.event_type,
            "agent": args.agent,
            "session_id": args.session_id,
            "cwd": str(cwd),
            "repo": git_context.get("repo"),
            "branch": git_context.get("branch"),
            "commit": git_context.get("commit"),
            "command": args.agent_command,
            "exit_code": args.exit_code,
            "duration_ms": args.duration_ms,
            "files_changed": files_changed,
            "semantic": semantic,
            "evidence": evidence,
        }
    )


def _handle_event(args: argparse.Namespace) -> int:
    event = _event_from_args(args)
    write_event(journal_root(), event)
    print("logged")
    return 0


def _report_date(args: argparse.Namespace) -> str:
    if args.date:
        return args.date
    if args.today:
        return datetime.now().astimezone().date().isoformat()
    return datetime.now().astimezone().date().isoformat()


def _handle_report(args: argparse.Namespace) -> int:
    date = _report_date(args)
    events = read_events_for_date(journal_root(), date)
    markdown = render_markdown_report(
        date,
        classify_daily_work(events),
        raw_event_count=len(events),
        provider_coverage=build_provider_coverage(events),
    )
    output = Path(args.output).expanduser() if args.output else journal_root() / "reports" / f"{date}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    if args.print_report:
        print(markdown)
    else:
        print(output)
    return 0


def _handle_status(args: argparse.Namespace) -> int:
    date = _report_date(args)
    events = read_events_for_date(journal_root(), date)
    classified = classify_daily_work(events)
    print(f"Date: {date}")
    print(f"Raw events: {len(events)}")
    print(f"Completed verified: {len(classified['completed_verified'])}")
    print(f"Completed claimed: {len(classified['completed_claimed'])}")
    print(f"Session summaries: {len(classified['session_summaries'])}")
    print(f"In progress: {len(classified['in_progress'])}")
    print(f"Blocked: {len(classified['blocked'])}")
    print(f"Notes: {len(classified['notes'])}")
    print(f"Risky: {len(classified['risky'])}")
    for agent, stats in build_provider_coverage(events).items():
        print(
            f"{agent}: {stats['sessions']} sessions, {stats['summarized']} summarized, "
            f"{stats['missing']} missing, {stats['in_progress']} in progress, "
            f"{stats['coverage_percent']}% coverage"
        )
    return 0


def _handle_doctor(args: argparse.Namespace) -> int:
    date = _report_date(args)
    result = build_doctor_result(journal_root(), date)
    print(build_doctor_report(result), end="")
    return 0


def _handle_web(args: argparse.Namespace) -> int:
    run_web_server(
        journal_root(),
        args.host,
        args.port,
        args.date,
        refresh_ms=args.refresh_ms,
        api_token=args.token,
    )
    return 0


def _handle_install(args: argparse.Namespace) -> int:
    if args.install_target == "wrappers":
        installed = install_wrappers(journal_root())
        for agent, path in installed.items():
            print(f"{agent}: {path}")
        print(f'Add this to PATH before real agent binaries: export PATH="{journal_root() / "bin"}:$PATH"')
        return 0
    if args.install_target == "shell-profile":
        for path in install_shell_profile(journal_root()):
            print(path)
        return 0
    if args.install_target == "agent-instructions":
        for agent, path in install_agent_instructions().items():
            print(f"{agent}: {path}")
        return 0
    if args.install_target == "git-hook":
        print(install_git_hook(args.repo))
        return 0
    if args.install_target == "mcp-snippets":
        root = Path.cwd()
        print("# Codex")
        print(codex_mcp_snippet(root))
        print("# Claude Code")
        print(claude_mcp_snippet(root))
        print("# Gemini CLI")
        print(gemini_mcp_snippet(root))
        return 0
    print("Choose an install target: wrappers", file=sys.stderr)
    return 2


def _event_matches_session(event: dict, session_id: str, agent: str) -> bool:
    if event.get("session_id") != session_id:
        return False
    return not event.get("agent") or event.get("agent") == agent


def _has_semantic_session_entry(events: list[dict], session_id: str, agent: str) -> bool:
    return any(
        _event_matches_session(event, session_id, agent)
        and (
            event.get("event_type") in SESSION_OUTCOME_EVENT_TYPES
            or (event.get("semantic") or {}).get("status") == "blocked"
        )
        for event in events
    )


def _has_guard_fallback(events: list[dict], session_id: str, agent: str) -> bool:
    return any(
        _event_matches_session(event, session_id, agent)
        and event.get("event_type") == "verification"
        and (event.get("semantic") or {}).get("status") == JOURNAL_MISSING_STATUS
        for event in events
    )


def _guard_fallback_event(args: argparse.Namespace) -> dict:
    cwd = Path.cwd()
    git_context = get_git_context(cwd)
    return normalize_event(
        {
            "event_type": "verification",
            "agent": args.agent,
            "session_id": args.session_id,
            "cwd": str(cwd),
            "repo": git_context.get("repo"),
            "branch": git_context.get("branch"),
            "commit": git_context.get("commit"),
            "files_changed": git_context.get("changed_files") or [],
            "semantic": {"status": JOURNAL_MISSING_STATUS, "note": args.note},
            "evidence": {
                "verification": "agent-journal guard session-end",
                "verification_status": "failed",
            },
        }
    )


def _handle_guard(args: argparse.Namespace) -> int:
    if args.guard_target == "session-end":
        root = journal_root()
        events = read_events_for_date(root, None)
        if _has_semantic_session_entry(events, args.session_id, args.agent):
            print("semantic journal entry exists")
            return 0
        if _has_guard_fallback(events, args.session_id, args.agent):
            print("guard already recorded missing semantic journal entry")
            return 0
        write_event(root, _guard_fallback_event(args))
        print("guarded: missing semantic journal entry")
        return 0
    print("Choose a guard target: session-end", file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    if args.command == "event":
        return _handle_event(args)
    if args.command == "report":
        return _handle_report(args)
    if args.command == "status":
        return _handle_status(args)
    if args.command == "doctor":
        return _handle_doctor(args)
    if args.command == "web":
        return _handle_web(args)
    if args.command == "install":
        return _handle_install(args)
    if args.command == "guard":
        return _handle_guard(args)
    parser.print_help()
    return 0


def entrypoint() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    entrypoint()
