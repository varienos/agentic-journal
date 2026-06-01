from __future__ import annotations

from typing import Any


def _label(event: dict[str, Any]) -> str:
    semantic = event.get("semantic") or {}
    task_id = _task_id(event)
    note = semantic.get("summary") or semantic.get("note") or semantic.get("reason")
    outcome = semantic.get("outcome")
    commit = event.get("commit")
    repo = event.get("repo") or event.get("cwd") or "unknown repo"
    agent = event.get("agent") or "unknown agent"
    bits = []
    if task_id:
        bits.append(task_id)
    if commit:
        bits.append(str(commit)[:12])
    if note:
        bits.append(note)
    if outcome:
        bits.append(f"outcome={outcome}")
    bits.append(f"agent={agent}")
    bits.append(f"repo={repo}")
    return " - ".join(bits)


def _task_id(event: dict[str, Any]) -> str | None:
    semantic = event.get("semantic") or {}
    return semantic.get("task_id") or event.get("task_id")


def _repos_compatible(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_repo = left.get("repo")
    right_repo = right.get("repo")
    return not left_repo or not right_repo or left_repo == right_repo


def _matches_passed_verification(event: dict[str, Any], verification: dict[str, Any]) -> bool:
    if not _repos_compatible(event, verification):
        return False

    if event.get("commit") and event.get("commit") == verification.get("commit"):
        return True

    if event.get("session_id") and event.get("session_id") == verification.get("session_id"):
        return True

    task_id = _task_id(event)
    return bool(task_id and task_id == _task_id(verification))


def _session_key(event: dict[str, Any]) -> tuple[str, str] | None:
    session_id = event.get("session_id")
    if not session_id:
        return None
    return (event.get("agent") or "unknown agent", session_id)


def classify_daily_work(events: list[dict[str, Any]]) -> dict[str, list[str]]:
    classified: dict[str, list[str]] = {
        "completed_verified": [],
        "completed_claimed": [],
        "session_summaries": [],
        "in_progress": [],
        "blocked": [],
        "notes": [],
        "risky": [],
    }
    passed_verification_by_commit: set[str] = set()
    passed_verifications: list[dict[str, Any]] = []
    commits: list[dict[str, Any]] = []
    closed_sessions: set[tuple[str, str]] = set()

    for event in events:
        evidence = event.get("evidence") or {}
        event_type = event.get("event_type")
        session_key = _session_key(event)
        if event_type in {"session_summary", "task_completed_claim", "task_blocked"} and session_key:
            closed_sessions.add(session_key)
        if (
            event_type == "verification"
            and evidence.get("verification_status") == "passed"
        ):
            passed_verifications.append(event)
            if event.get("commit"):
                passed_verification_by_commit.add(event["commit"])
        if event_type == "verification" and evidence.get("verification_status") == "failed" and session_key:
            closed_sessions.add(session_key)
        if event_type == "git_commit":
            commits.append(event)

    for event in commits:
        if event.get("commit") and event.get("commit") in passed_verification_by_commit:
            classified["completed_verified"].append(_label(event))
        elif event.get("commit"):
            classified["in_progress"].append(_label(event))

    for event in events:
        event_type = event.get("event_type")
        evidence = event.get("evidence") or {}
        semantic = event.get("semantic") or {}
        if event_type == "task_completed_claim":
            if any(_matches_passed_verification(event, verification) for verification in passed_verifications):
                classified["completed_verified"].append(_label(event))
            else:
                classified["completed_claimed"].append(_label(event))
        elif event_type == "session_summary":
            classified["session_summaries"].append(_label(event))
        elif event_type == "task_blocked" or semantic.get("status") == "blocked":
            classified["blocked"].append(_label(event))
        elif event_type == "semantic_note":
            classified["notes"].append(_label(event))
        elif event_type == "agent_end" and event.get("exit_code") not in (None, 0):
            classified["risky"].append(_label(event))
        elif event_type == "verification" and evidence.get("verification_status") == "failed":
            classified["risky"].append(_label(event))
        elif event_type == "agent_start":
            if _session_key(event) not in closed_sessions:
                classified["in_progress"].append(_label(event))

    return classified


def render_markdown_report(date: str, classified: dict[str, list[str]], raw_event_count: int) -> str:
    lines = [
        f"# {date} Agent Journal",
        "",
        "## Summary",
        f"- Completed verified: {len(classified.get('completed_verified', []))}",
        f"- Completed claimed: {len(classified.get('completed_claimed', []))}",
        f"- Session summaries: {len(classified.get('session_summaries', []))}",
        f"- In progress: {len(classified.get('in_progress', []))}",
        f"- Blocked: {len(classified.get('blocked', []))}",
        f"- Notes: {len(classified.get('notes', []))}",
        f"- Risky / needs review: {len(classified.get('risky', []))}",
        "",
    ]

    sections = [
        ("Completed Verified", "completed_verified"),
        ("Completed Claimed", "completed_claimed"),
        ("Session Summaries", "session_summaries"),
        ("In Progress", "in_progress"),
        ("Blocked", "blocked"),
        ("Notes", "notes"),
        ("Risky / Needs Review", "risky"),
    ]
    for title, key in sections:
        lines.append(f"## {title}")
        items = classified.get(key, [])
        if not items:
            lines.append("- None")
        else:
            lines.extend(f"- {item}" for item in items)
        lines.append("")

    lines.extend(["## Raw Event Count", f"- {raw_event_count}", ""])
    return "\n".join(lines)
