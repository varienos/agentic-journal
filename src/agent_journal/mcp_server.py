from __future__ import annotations

import os
from pathlib import Path

from agent_journal.events import normalize_event
from agent_journal.git_context import get_git_context
from agent_journal.storage import read_events_for_date, write_event


def _event_context(session_id: str | None = None) -> dict:
    cwd = Path.cwd()
    git_context = get_git_context(cwd)
    return {
        "session_id": session_id or os.environ.get("AGENT_JOURNAL_SESSION_ID"),
        "cwd": str(cwd),
        "repo": git_context.get("repo"),
        "branch": git_context.get("branch"),
        "commit": git_context.get("commit"),
    }


def journal_note(
    journal_home: str | Path | None = None,
    agent: str = "unknown",
    note: str = "",
    session_id: str | None = None,
) -> str:
    event = normalize_event(
        {
            "event_type": "semantic_note",
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
            "event_type": "task_completed_claim",
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
            "event_type": "session_summary",
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
            "event_type": "task_blocked",
            "agent": agent,
            **_event_context(session_id),
            "semantic": {"task_id": task_id, "status": "blocked", "reason": reason},
        }
    )
    write_event(journal_home, event)
    return "logged"


def journal_daily_report(journal_home: str | Path | None = None, date: str | None = None) -> str:
    # Import lazily so the lightweight semantic write helpers stay dependency-free.
    from agent_journal.report import classify_daily_work, render_markdown_report

    events = read_events_for_date(journal_home, date)
    report_date = date or (events[-1]["ts"][:10] if events else "today")
    markdown = render_markdown_report(report_date, classify_daily_work(events), raw_event_count=len(events))
    root = Path(journal_home).expanduser() if journal_home else Path.home() / ".agent-journal"
    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{report_date}.md"
    path.write_text(markdown, encoding="utf-8")
    return f"report: {path}"


def create_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("The 'mcp' package is required to run agent-journal-mcp") from exc

    server = FastMCP("agent-journal")

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
