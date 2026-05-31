from __future__ import annotations

from collections import defaultdict
from typing import Any


def _label(event: dict[str, Any]) -> str:
    semantic = event.get("semantic") or {}
    task_id = semantic.get("task_id")
    note = semantic.get("note") or semantic.get("reason")
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
    bits.append(f"agent={agent}")
    bits.append(f"repo={repo}")
    return " - ".join(bits)


def classify_daily_work(events: list[dict[str, Any]]) -> dict[str, list[str]]:
    classified: dict[str, list[str]] = {
        "completed_verified": [],
        "completed_claimed": [],
        "in_progress": [],
        "blocked": [],
        "risky": [],
    }
    passed_verification_by_repo: defaultdict[str, bool] = defaultdict(bool)
    commits: list[dict[str, Any]] = []

    for event in events:
        repo = event.get("repo") or event.get("cwd") or ""
        evidence = event.get("evidence") or {}
        if event.get("event_type") == "verification" and evidence.get("verification_status") == "passed":
            passed_verification_by_repo[repo] = True
        if event.get("event_type") == "git_commit":
            commits.append(event)

    verified_commits = set()
    for event in commits:
        repo = event.get("repo") or event.get("cwd") or ""
        if event.get("commit") and passed_verification_by_repo[repo]:
            classified["completed_verified"].append(_label(event))
            verified_commits.add(event.get("commit"))
        elif event.get("commit"):
            classified["in_progress"].append(_label(event))

    for event in events:
        event_type = event.get("event_type")
        evidence = event.get("evidence") or {}
        semantic = event.get("semantic") or {}
        if event_type == "task_completed_claim":
            classified["completed_claimed"].append(_label(event))
        elif event_type == "task_blocked" or semantic.get("status") == "blocked":
            classified["blocked"].append(_label(event))
        elif event_type == "agent_end" and event.get("exit_code") not in (None, 0):
            classified["risky"].append(_label(event))
        elif event_type == "verification" and evidence.get("verification_status") == "failed":
            classified["risky"].append(_label(event))
        elif event_type == "agent_start":
            classified["in_progress"].append(_label(event))

    return classified


def render_markdown_report(date: str, classified: dict[str, list[str]], raw_event_count: int) -> str:
    lines = [
        f"# {date} Agent Journal",
        "",
        "## Summary",
        f"- Completed verified: {len(classified.get('completed_verified', []))}",
        f"- Completed claimed: {len(classified.get('completed_claimed', []))}",
        f"- In progress: {len(classified.get('in_progress', []))}",
        f"- Blocked: {len(classified.get('blocked', []))}",
        f"- Risky / needs review: {len(classified.get('risky', []))}",
        "",
    ]

    sections = [
        ("Completed Verified", "completed_verified"),
        ("Completed Claimed", "completed_claimed"),
        ("In Progress", "in_progress"),
        ("Blocked", "blocked"),
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

