from agentic_journal.report import (
    build_provider_coverage,
    classify_daily_work,
    event_label,
    event_task_id,
    render_markdown_report,
)


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


def test_public_event_label_helpers_are_available():
    event = {
        "event_type": "semantic_note",
        "agent": "codex",
        "repo": "/repo",
        "semantic": {"task_id": "TASK-1", "note": "Reviewed"},
    }

    assert event_task_id(event) == "TASK-1"
    assert event_label(event) == "TASK-1 - Reviewed - agent=codex - repo=/repo"


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


def test_session_verification_does_not_leak_across_different_tasks():
    # A passed verification for TASK-A must not verify an unrelated claim for
    # TASK-B that merely shares the same session_id.
    items = classify_daily_work(
        [
            {
                "event_type": "task_completed_claim",
                "agent": "codex",
                "session_id": "session-1",
                "repo": "/repo",
                "semantic": {"task_id": "TASK-B", "note": "Unverified work"},
            },
            {
                "event_type": "verification",
                "agent": "codex",
                "session_id": "session-1",
                "repo": "/repo",
                "semantic": {"task_id": "TASK-A"},
                "evidence": {"verification_status": "passed", "verification": "pytest"},
            },
        ]
    )

    assert items["completed_verified"] == []
    assert items["completed_claimed"] == ["TASK-B - Unverified work - agent=codex - repo=/repo"]


def test_claim_and_verification_with_all_empty_keys_stays_claimed():
    # No commit / session_id / task_id on either side must never cross-verify.
    items = classify_daily_work(
        [
            {"event_type": "task_completed_claim", "agent": "codex", "semantic": {"note": "Done"}},
            {
                "event_type": "verification",
                "agent": "codex",
                "evidence": {"verification_status": "passed"},
            },
        ]
    )

    assert items["completed_verified"] == []
    assert items["completed_claimed"] == ["Done - agent=codex - repo=unknown repo"]


def test_failed_agent_end_is_risky():
    items = classify_daily_work(
        [{"event_type": "agent_end", "agent": "claude", "exit_code": 1, "repo": "/repo"}]
    )

    assert items["risky"]


def test_clean_agent_end_is_not_risky():
    items = classify_daily_work(
        [{"event_type": "agent_end", "agent": "claude", "exit_code": 0, "repo": "/repo"}]
    )

    assert items["risky"] == []


def test_failed_agent_end_closes_matching_agent_start():
    # A session that errored out should not appear in both Risky and In Progress.
    items = classify_daily_work(
        [
            {"event_type": "agent_start", "agent": "codex", "session_id": "s1", "repo": "/repo"},
            {
                "event_type": "agent_end",
                "agent": "codex",
                "session_id": "s1",
                "exit_code": 7,
                "repo": "/repo",
            },
        ]
    )

    assert items["risky"]
    assert items["in_progress"] == []


def test_task_blocked_is_reported_as_blocked():
    items = classify_daily_work(
        [
            {
                "event_type": "task_blocked",
                "agent": "gemini",
                "repo": "/repo",
                "semantic": {"task_id": "TASK-3", "status": "blocked", "reason": "waiting on API"},
            }
        ]
    )

    assert items["blocked"] == ["TASK-3 - waiting on API - agent=gemini - repo=/repo"]


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


def test_session_summary_is_reported_as_session_summary():
    items = classify_daily_work(
        [
            {
                "event_type": "session_summary",
                "agent": "codex",
                "session_id": "session-1",
                "repo": "/repo",
                "semantic": {
                    "task_id": "TASK-8",
                    "summary": "Implemented session summary logging",
                    "outcome": "completed",
                },
            }
        ]
    )

    assert items["session_summaries"] == [
        "TASK-8 - Implemented session summary logging - outcome=completed - agent=codex - repo=/repo"
    ]


def test_model_operation_is_reported_as_model_activity():
    items = classify_daily_work(
        [
            {
                "event_type": "model_operation",
                "agent": "cortex",
                "session_id": "chat-1",
                "repo": "/repo",
                "duration_ms": 1234,
                "semantic": {
                    "provider": "claude",
                    "model": "claude-opus-4-8-thinking-high",
                    "operation": "chat",
                    "source": "/api/chat",
                    "status": "completed",
                },
                "evidence": {"token_usage": {"input_tokens": 1200, "output_tokens": 340}},
            }
        ]
    )

    assert items["model_activity"] == [
        "chat - claude/claude-opus-4-8-thinking-high - status=completed - source=/api/chat - 1540 tokens - 1234ms - agent=cortex - repo=/repo"
    ]
    assert items["in_progress"] == []


def test_session_summary_closes_matching_agent_start_in_report():
    items = classify_daily_work(
        [
            {
                "event_type": "agent_start",
                "agent": "codex",
                "session_id": "session-1",
                "repo": "/repo",
            },
            {
                "event_type": "session_summary",
                "agent": "codex",
                "session_id": "session-1",
                "repo": "/repo",
                "semantic": {
                    "summary": "Implemented session summary logging",
                    "outcome": "completed",
                },
            },
        ]
    )

    assert items["session_summaries"] == [
        "Implemented session summary logging - outcome=completed - agent=codex - repo=/repo"
    ]
    assert items["in_progress"] == []


def test_render_markdown_report_includes_required_sections():
    markdown = render_markdown_report(
        "2026-05-31",
        classify_daily_work([]),
        raw_event_count=0,
        provider_coverage={
            "codex": {
                "sessions": 0,
                "summarized": 0,
                "missing": 0,
                "in_progress": 0,
                "coverage_percent": 0,
            }
        },
    )

    assert "# 2026-05-31 Agentic Journal" in markdown
    assert "Evidence Levels" in markdown
    assert "Verified Work" in markdown
    assert "Model Activity" in markdown
    assert "Provider Coverage" in markdown
    assert "codex: 0 sessions, 0 summarized, 0 missing, 0 in progress, 0% coverage" in markdown
    assert "Notes" in markdown
    assert "Risky / Needs Review" in markdown
    assert "Raw Event Count" in markdown


def test_build_provider_coverage_counts_summarized_missing_and_in_progress_sessions():
    coverage = build_provider_coverage(
        [
            {"event_type": "agent_start", "agent": "codex", "session_id": "c1"},
            {"event_type": "session_summary", "agent": "codex", "session_id": "c1"},
            {"event_type": "agent_start", "agent": "claude", "session_id": "cl1"},
            {
                "event_type": "verification",
                "agent": "claude",
                "session_id": "cl1",
                "semantic": {"status": "journal_missing"},
                "evidence": {"verification_status": "failed"},
            },
            {"event_type": "agent_start", "agent": "gemini", "session_id": "g1"},
        ]
    )

    assert coverage["codex"] == {
        "sessions": 1,
        "summarized": 1,
        "missing": 0,
        "in_progress": 0,
        "coverage_percent": 100,
    }
    assert coverage["claude"]["missing"] == 1
    assert coverage["gemini"]["in_progress"] == 1


def test_build_provider_coverage_normalizes_agent_aliases_and_ignores_no_session_events():
    coverage = build_provider_coverage(
        [
            {"event_type": "session_summary", "agent": "Codex", "semantic": {"summary": "No session id"}},
            {"event_type": "agent_start", "agent": "claude-code", "session_id": "cl1"},
            {"event_type": "task_blocked", "agent": "claude-code", "session_id": "cl1"},
        ]
    )

    assert set(coverage) == {"claude", "codex", "gemini"}
    assert coverage["claude"]["sessions"] == 1
    assert coverage["claude"]["summarized"] == 1
    assert coverage["codex"]["sessions"] == 0
