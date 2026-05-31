from agent_journal.report import classify_daily_work, render_markdown_report


def test_commit_with_verification_is_completed_verified():
    items = classify_daily_work(
        [
            {"event_type": "git_commit", "commit": "abc123", "repo": "/repo", "agent": "codex"},
            {
                "event_type": "verification",
                "repo": "/repo",
                "agent": "codex",
                "evidence": {"verification_status": "passed"},
            },
        ]
    )

    assert items["completed_verified"]


def test_completion_claim_without_commit_is_claimed():
    items = classify_daily_work(
        [
            {
                "event_type": "task_completed_claim",
                "agent": "gemini",
                "semantic": {"task_id": "TASK-1", "note": "Done"},
            }
        ]
    )

    assert items["completed_claimed"]


def test_failed_agent_end_is_risky():
    items = classify_daily_work(
        [{"event_type": "agent_end", "agent": "claude", "exit_code": 1, "repo": "/repo"}]
    )

    assert items["risky"]


def test_render_markdown_report_includes_required_sections():
    markdown = render_markdown_report("2026-05-31", classify_daily_work([]), raw_event_count=0)

    assert "# 2026-05-31 Agent Journal" in markdown
    assert "Completed Verified" in markdown
    assert "Risky / Needs Review" in markdown
    assert "Raw Event Count" in markdown

