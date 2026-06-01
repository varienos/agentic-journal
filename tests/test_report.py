from agent_journal.report import classify_daily_work, render_markdown_report


def test_commit_with_verification_is_completed_verified():
    items = classify_daily_work(
        [
            {"event_type": "git_commit", "commit": "abc123", "repo": "/repo", "agent": "codex"},
            {
                "event_type": "verification",
                "repo": "/repo",
                "commit": "abc123",
                "agent": "codex",
                "evidence": {"verification_status": "passed"},
            },
        ]
    )

    assert items["completed_verified"]


def test_verification_only_marks_matching_commit_verified():
    items = classify_daily_work(
        [
            {"event_type": "git_commit", "commit": "c1", "repo": "/repo", "agent": "git"},
            {"event_type": "git_commit", "commit": "c2", "repo": "/repo", "agent": "git"},
            {
                "event_type": "verification",
                "repo": "/repo",
                "commit": "c1",
                "agent": "codex",
                "evidence": {"verification_status": "passed"},
            },
        ]
    )

    assert items["completed_verified"] == ["c1 - agent=git - repo=/repo"]
    assert items["in_progress"] == ["c2 - agent=git - repo=/repo"]


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


def test_completion_claim_with_matching_session_verification_is_verified():
    items = classify_daily_work(
        [
            {
                "event_type": "task_completed_claim",
                "agent": "codex",
                "session_id": "session-1",
                "repo": "/repo",
                "semantic": {"task_id": "TASK-9", "note": "Done"},
            },
            {
                "event_type": "verification",
                "agent": "codex",
                "session_id": "session-1",
                "repo": "/repo",
                "evidence": {"verification_status": "passed", "verification": "pytest"},
            },
        ]
    )

    assert items["completed_verified"] == ["TASK-9 - Done - agent=codex - repo=/repo"]
    assert items["completed_claimed"] == []


def test_completion_claim_with_matching_task_verification_is_verified():
    items = classify_daily_work(
        [
            {
                "event_type": "task_completed_claim",
                "agent": "claude",
                "repo": "/repo",
                "semantic": {"task_id": "TASK-10", "note": "Implemented"},
            },
            {
                "event_type": "verification",
                "agent": "codex",
                "repo": "/repo",
                "semantic": {"task_id": "TASK-10"},
                "evidence": {"verification_status": "passed", "verification": "scripts/verify.sh"},
            },
        ]
    )

    assert items["completed_verified"] == ["TASK-10 - Implemented - agent=claude - repo=/repo"]
    assert items["completed_claimed"] == []


def test_completion_claim_with_legacy_top_level_task_id_verification_is_verified():
    items = classify_daily_work(
        [
            {
                "event_type": "task_completed_claim",
                "agent": "gemini",
                "repo": "/repo",
                "task_id": "TASK-11",
                "semantic": {"note": "Legacy writer"},
            },
            {
                "event_type": "verification",
                "agent": "codex",
                "repo": "/repo",
                "task_id": "TASK-11",
                "evidence": {"verification_status": "passed", "verification": "pytest"},
            },
        ]
    )

    assert items["completed_verified"] == ["TASK-11 - Legacy writer - agent=gemini - repo=/repo"]


def test_completion_claim_with_mismatched_repo_task_verification_stays_claimed():
    items = classify_daily_work(
        [
            {
                "event_type": "task_completed_claim",
                "agent": "claude",
                "repo": "/repo-a",
                "semantic": {"task_id": "TASK-10", "note": "Implemented"},
            },
            {
                "event_type": "verification",
                "agent": "codex",
                "repo": "/repo-b",
                "semantic": {"task_id": "TASK-10"},
                "evidence": {"verification_status": "passed", "verification": "scripts/verify.sh"},
            },
        ]
    )

    assert items["completed_verified"] == []
    assert items["completed_claimed"] == ["TASK-10 - Implemented - agent=claude - repo=/repo-a"]


def test_failed_agent_end_is_risky():
    items = classify_daily_work(
        [{"event_type": "agent_end", "agent": "claude", "exit_code": 1, "repo": "/repo"}]
    )

    assert items["risky"]


def test_semantic_notes_are_reported_as_notes():
    items = classify_daily_work(
        [
            {
                "event_type": "semantic_note",
                "agent": "claude",
                "repo": "/repo",
                "semantic": {"note": "Claude MCP bağlantısı test edildi"},
            }
        ]
    )

    assert items["notes"] == ["Claude MCP bağlantısı test edildi - agent=claude - repo=/repo"]


def test_render_markdown_report_includes_required_sections():
    markdown = render_markdown_report("2026-05-31", classify_daily_work([]), raw_event_count=0)

    assert "# 2026-05-31 Agent Journal" in markdown
    assert "Completed Verified" in markdown
    assert "Notes" in markdown
    assert "Risky / Needs Review" in markdown
    assert "Raw Event Count" in markdown
