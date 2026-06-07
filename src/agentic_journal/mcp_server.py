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
    event = normalize_event(
        {
            "event_type": SEMANTIC_NOTE_EVENT_TYPE,
            "agent": agent,
            **_event_context(session_id),
            "semantic": {"note": note},
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
    event = normalize_event(
        {
            "event_type": TASK_COMPLETED_CLAIM_EVENT_TYPE,
            "agent": agent,
            **_event_context(session_id),
            "semantic": {"task_id": task_id, "status": "completed_claimed", "note": note},
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
    semantic = {"summary": summary, "outcome": outcome}
    if task_id:
        semantic["task_id"] = task_id
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
    event = normalize_event(
        {
            "event_type": TASK_BLOCKED_EVENT_TYPE,
            "agent": agent,
            **_event_context(session_id),
            "semantic": {"task_id": task_id, "status": "blocked", "reason": reason},
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
