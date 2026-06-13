from __future__ import annotations

import os
from pathlib import Path

from agentic_journal.events import (
    SEMANTIC_NOTE_EVENT_TYPE,
    SESSION_SUMMARY_EVENT_TYPE,
    TASK_BLOCKED_EVENT_TYPE,
    TASK_COMPLETED_CLAIM_EVENT_TYPE,
    normalize_event,
)
from agentic_journal.git_context import event_context
from agentic_journal.storage import write_event

SKIPPED_NOTE_REQUIRED = "skipped: note is required"
SKIPPED_SUMMARY_REQUIRED = "skipped: summary is required"
SKIPPED_TASK_OR_NOTE_REQUIRED = "skipped: task_id or note is required"
SKIPPED_REASON_REQUIRED = "skipped: reason is required"


def _clean_text(value: str | None) -> str:
    return value.strip() if isinstance(value, str) else ""


def _event_context(session_id: str | None = None) -> dict:
    return {
        "session_id": session_id
        or os.environ.get("AGENTIC_JOURNAL_SESSION_ID")
        or os.environ.get("AGENT_JOURNAL_SESSION_ID"),
        **event_context(Path.cwd()),
    }


def journal_note(
    journal_home: str | Path | None = None,
    agent: str = "unknown",
    note: str = "",
    session_id: str | None = None,
) -> str:
    note_text = _clean_text(note)
    if not note_text:
        return SKIPPED_NOTE_REQUIRED
    event = normalize_event(
        {
            "event_type": SEMANTIC_NOTE_EVENT_TYPE,
            "agent": agent,
            **_event_context(session_id),
            "semantic": {"note": note_text},
        }
    )
    write_event(journal_home, event)
    return "logged"


def journal_task_completed(
    journal_home: str | Path | None = None,
    agent: str = "unknown",
    task_id: str | None = None,
    note: str = "",
    session_id: str | None = None,
) -> str:
    task_text = _clean_text(task_id)
    note_text = _clean_text(note)
    if not task_text and not note_text:
        return SKIPPED_TASK_OR_NOTE_REQUIRED
    semantic = {"status": "completed_claimed"}
    if task_text:
        semantic["task_id"] = task_text
    if note_text:
        semantic["note"] = note_text
    event = normalize_event(
        {
            "event_type": TASK_COMPLETED_CLAIM_EVENT_TYPE,
            "agent": agent,
            **_event_context(session_id),
            "semantic": semantic,
        }
    )
    write_event(journal_home, event)
    return "logged"


def journal_session_summary(
    journal_home: str | Path | None = None,
    agent: str = "unknown",
    session_id: str | None = None,
    task_id: str | None = None,
    summary: str = "",
    outcome: str = "unknown",
) -> str:
    summary_text = _clean_text(summary)
    if not summary_text:
        return SKIPPED_SUMMARY_REQUIRED
    semantic = {"summary": summary_text, "outcome": _clean_text(outcome) or "unknown"}
    task_text = _clean_text(task_id)
    if task_text:
        semantic["task_id"] = task_text
    event = normalize_event(
        {
            "event_type": SESSION_SUMMARY_EVENT_TYPE,
            "agent": agent,
            **_event_context(session_id),
            "semantic": semantic,
        }
    )
    write_event(journal_home, event)
    return "logged"


def journal_task_blocked(
    journal_home: str | Path | None = None,
    agent: str = "unknown",
    task_id: str | None = None,
    reason: str = "",
    session_id: str | None = None,
) -> str:
    reason_text = _clean_text(reason)
    if not reason_text:
        return SKIPPED_REASON_REQUIRED
    semantic = {"status": "blocked", "reason": reason_text}
    task_text = _clean_text(task_id)
    if task_text:
        semantic["task_id"] = task_text
    event = normalize_event(
        {
            "event_type": TASK_BLOCKED_EVENT_TYPE,
            "agent": agent,
            **_event_context(session_id),
            "semantic": semantic,
        }
    )
    write_event(journal_home, event)
    return "logged"


def journal_daily_report(journal_home: str | Path | None = None, date: str | None = None) -> str:
    # Import lazily so the lightweight semantic write helpers stay dependency-free.
    from agentic_journal.config import journal_root, secure_dir, secure_file
    from agentic_journal.report import render_daily_report

    root = Path(journal_home).expanduser() if journal_home else journal_root()
    report_date, markdown, _ = render_daily_report(root, date)
    report_dir = secure_dir(root / "reports")
    path = report_dir / f"{report_date}.md"
    path.write_text(markdown, encoding="utf-8")
    secure_file(path)
    return f"report: {path}"


def create_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("The 'mcp' package is required to run agentic-journal-mcp") from exc

    server = FastMCP("agentic-journal")

    @server.tool(name="journal_note")
    def journal_note_tool(agent: str = "unknown", note: str = "", session_id: str = "") -> str:
        return journal_note(agent=agent, note=note, session_id=session_id or None)

    @server.tool(name="journal_session_summary")
    def journal_session_summary_tool(
        agent: str = "unknown",
        session_id: str = "",
        task_id: str = "",
        summary: str = "",
        outcome: str = "unknown",
    ) -> str:
        return journal_session_summary(
            agent=agent,
            session_id=session_id or None,
            task_id=task_id or None,
            summary=summary,
            outcome=outcome,
        )

    @server.tool(name="journal_task_completed")
    def journal_task_completed_tool(
        agent: str = "unknown",
        task_id: str = "",
        note: str = "",
        session_id: str = "",
    ) -> str:
        return journal_task_completed(agent=agent, task_id=task_id, note=note, session_id=session_id or None)

    @server.tool(name="journal_task_blocked")
    def journal_task_blocked_tool(
        agent: str = "unknown",
        task_id: str = "",
        reason: str = "",
        session_id: str = "",
    ) -> str:
        return journal_task_blocked(agent=agent, task_id=task_id, reason=reason, session_id=session_id or None)

    @server.tool(name="journal_daily_report")
    def journal_daily_report_tool(date: str = "") -> str:
        return journal_daily_report(date=date or None)

    return server


def main() -> None:
    create_mcp_server().run()
