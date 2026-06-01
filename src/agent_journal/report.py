from __future__ import annotations

from typing import Any


DEFAULT_PROVIDERS = ("codex", "claude", "gemini")
SESSION_OUTCOME_EVENT_TYPES = {"session_summary", "task_completed_claim", "task_blocked"}
SESSION_EVENT_TYPES = SESSION_OUTCOME_EVENT_TYPES | {"agent_start", "agent_end", "verification"}
JOURNAL_MISSING_STATUS = "journal_missing"
AGENT_ALIASES = {
    "claude-code": "claude",
}


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


def _provider_name(agent: str | None) -> str:
    normalized = (agent or "unknown").strip().lower()
    return AGENT_ALIASES.get(normalized, normalized)


def build_provider_coverage(events: list[dict[str, Any]], providers: tuple[str, ...] = DEFAULT_PROVIDERS) -> dict[str, dict[str, int]]:
    sessions: dict[str, set[str]] = {provider: set() for provider in providers}
    summarized: dict[str, set[str]] = {provider: set() for provider in providers}
    missing: dict[str, set[str]] = {provider: set() for provider in providers}

    for event in events:
        session_id = event.get("session_id")
        if not session_id:
            continue
        agent = _provider_name(event.get("agent"))
        if agent not in sessions:
            sessions[agent] = set()
            summarized[agent] = set()
            missing[agent] = set()
        event_type = event.get("event_type")
        semantic = event.get("semantic") or {}
        if event_type in SESSION_EVENT_TYPES:
            sessions[agent].add(session_id)
        if event_type in SESSION_OUTCOME_EVENT_TYPES:
            summarized[agent].add(session_id)
        if event_type == "verification" and semantic.get("status") == JOURNAL_MISSING_STATUS:
            missing[agent].add(session_id)

    coverage: dict[str, dict[str, int]] = {}
    for agent in sorted(sessions):
        total = len(sessions[agent])
        summarized_count = len(summarized[agent])
        missing_count = len(missing[agent])
        in_progress = max(0, total - summarized_count - missing_count)
        coverage[agent] = {
            "sessions": total,
            "summarized": summarized_count,
            "missing": missing_count,
            "in_progress": in_progress,
            "coverage_percent": round((summarized_count / total) * 100) if total else 0,
        }
    return coverage


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
        if event_type in SESSION_OUTCOME_EVENT_TYPES and session_key:
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


def _render_provider_coverage(provider_coverage: dict[str, dict[str, int]]) -> list[str]:
    if not provider_coverage:
        return ["- None"]
    lines = []
    for agent, stats in sorted(provider_coverage.items()):
        lines.append(
            "- "
            f"{agent}: {stats['sessions']} sessions, "
            f"{stats['summarized']} summarized, "
            f"{stats['missing']} missing, "
            f"{stats['in_progress']} in progress, "
            f"{stats['coverage_percent']}% coverage"
        )
    return lines


def render_markdown_report(
    date: str,
    classified: dict[str, list[str]],
    raw_event_count: int,
    provider_coverage: dict[str, dict[str, int]] | None = None,
) -> str:
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
        "## Evidence Levels",
        "- Verified: commit or task work backed by matching passed verification.",
        "- Claimed: agent reported completion, but matching verification is missing.",
        "- Observed: session or commit activity exists without completion evidence yet.",
        "- Risky: failed verification, missing semantic summary, or non-zero agent exit.",
        "",
        "## Provider Coverage",
        *_render_provider_coverage(provider_coverage or {}),
        "",
    ]

    sections = [
        ("Verified Work (Completed Verified)", "completed_verified"),
        ("Claimed Work (Completed Claimed)", "completed_claimed"),
        ("Session Outcomes", "session_summaries"),
        ("Observed / In Progress", "in_progress"),
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
