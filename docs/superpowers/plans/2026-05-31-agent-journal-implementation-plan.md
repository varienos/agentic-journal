# Agent Journal Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local observer-first journal that records what Codex, Claude Code, and Gemini CLI worked on during the day and produces an end-of-day evidence-based report.

**Architecture:** Agent Journal treats observable facts as ground truth: CLI invocations, git commits, changed files, command exit codes, and test results. MCP is added as a semantic annotation layer so agents can attach notes, task IDs, and blocked/completed claims, but verified completion always comes from evidence.

**Tech Stack:** Python 3.11+, SQLite WAL, JSONL event mirror, stdio MCP server, POSIX shell wrappers, git hooks, pytest.

---

## Product Definition

Agent Journal answers one daily question:

> "Codex, Claude, and Gemini worked today. What actually got done, what is still in progress, and what needs review?"

The first useful version must work locally without a hosted service. It should not depend on model memory or model honesty. It should survive multiple repos, multiple agents, and sessions started from different terminals.

## Core Principles

- Evidence first: commits, diffs, commands, exit codes, and test results are stronger than agent self-reporting.
- MCP second: MCP tools add semantic notes, task IDs, and status claims.
- Privacy by default: do not log full prompts, full tool arguments, API keys, or file contents in MVP.
- Local first: all data lives under `~/.agent-journal`.
- Small responses: MCP tools return short acknowledgements to avoid wasting model context.
- Append-only events: raw events are immutable; reports are derived views.

## Status Vocabulary

- `completed_verified`: commit exists and supporting evidence exists, such as passing tests or explicit verification command.
- `completed_claimed`: an agent marked the work complete, but no commit or verification evidence exists.
- `in_progress`: there are uncommitted changes, an open session, or a task note without completion evidence.
- `blocked`: agent or observer recorded a blocker.
- `risky`: failed command, failed test, non-zero agent exit, crash, or missing evidence after a completion claim.

## Repository Layout

Create the project under:

`/Users/varienos/Landing/Repo/agent-journal`

Planned files:

```text
agent-journal/
  README.md
  pyproject.toml
  src/
    agent_journal/
      __init__.py
      cli.py
      config.py
      events.py
      git_context.py
      storage.py
      report.py
      security.py
      install.py
      mcp_server.py
  scripts/
    wrappers/
      agent-journal-wrapper.sh
    hooks/
      post-commit
  tests/
    test_events.py
    test_storage.py
    test_report.py
    test_git_context.py
    test_security.py
    test_cli.py
    test_install.py
    test_mcp_server.py
  docs/
    event-schema.md
    operations.md
    superpowers/
      plans/
        2026-05-31-agent-journal-implementation-plan.md
```

Runtime files:

```text
~/.agent-journal/
  config.toml
  agent-journal.db
  events/
    2026-05-31.jsonl
  reports/
    2026-05-31.md
  bin/
    codex
    claude
    gemini
```

## Event Schema

MVP event shape:

```json
{
  "schema_version": 1,
  "event_id": "uuid",
  "ts": "2026-05-31T23:00:00+03:00",
  "event_type": "agent_end",
  "agent": "codex",
  "session_id": "uuid-or-wrapper-id",
  "cwd": "/Users/varienos/Landing/Herd/dev.ybs",
  "repo": "/Users/varienos/Landing/Herd/dev.ybs",
  "branch": "feature/invoice-filter",
  "commit": null,
  "command": "codex",
  "exit_code": 0,
  "duration_ms": 12345,
  "files_changed": [],
  "semantic": {
    "task_id": "TASK-42",
    "status": "completed_claimed",
    "note": "Fatura filtreleme düzeltildi"
  },
  "evidence": {
    "verification": "npm test",
    "verification_status": "passed"
  }
}
```

Allowed `event_type` values for MVP:

- `agent_start`
- `agent_end`
- `git_commit`
- `verification`
- `semantic_note`
- `task_completed_claim`
- `task_blocked`

## Chunk 1: Project Bootstrap

### Task 1: Initialize Python Package

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/pyproject.toml`
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/__init__.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/cli.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_cli.py`

- [ ] **Step 1: Write CLI smoke test**

```python
from agent_journal.cli import main


def test_main_help_exits_cleanly(capsys):
    exit_code = main(["--help"])
    assert exit_code == 0
    assert "agent-journal" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_cli.py -q
```

Expected: FAIL because `agent_journal.cli` does not exist yet.

- [ ] **Step 3: Add minimal package and CLI**

Implement `pyproject.toml` with:

- package name: `agent-journal`
- console script: `agent-journal = agent_journal.cli:entrypoint`
- dev dependency group with `pytest`

Implement `main(argv=None)` using `argparse`.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src tests
git commit -m "chore: bootstrap agent-journal package"
```

## Chunk 2: Append-Only Event Writer

### Task 2: Define Event Model and Validation

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/events.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_events.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/docs/event-schema.md`

- [ ] **Step 1: Write event normalization tests**

```python
from agent_journal.events import normalize_event


def test_normalize_event_adds_required_fields():
    event = normalize_event({"event_type": "agent_start", "agent": "codex"})

    assert event["schema_version"] == 1
    assert event["event_id"]
    assert event["ts"]
    assert event["event_type"] == "agent_start"
    assert event["agent"] == "codex"


def test_normalize_event_rejects_unknown_event_type():
    try:
        normalize_event({"event_type": "unknown", "agent": "codex"})
    except ValueError as exc:
        assert "event_type" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_events.py -q
```

Expected: FAIL because `events.py` is not implemented.

- [ ] **Step 3: Implement event normalization**

Add:

- `ALLOWED_EVENT_TYPES`
- `normalize_event(raw: dict) -> dict`
- UTC/local ISO timestamp generation
- UUID event IDs
- default empty `semantic` and `evidence` dicts

- [ ] **Step 4: Document schema**

Write `docs/event-schema.md` with:

- required fields
- optional fields
- event type meanings
- privacy rules

- [ ] **Step 5: Run test**

```bash
pytest tests/test_events.py -q
```

Expected: PASS.

### Task 3: JSONL Storage

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/storage.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_storage.py`

- [ ] **Step 1: Write JSONL append/read tests**

```python
from agent_journal.storage import append_jsonl_event, read_jsonl_events


def test_append_jsonl_event_writes_by_date(tmp_path):
    root = tmp_path / "journal"
    event = {
        "schema_version": 1,
        "event_id": "e1",
        "ts": "2026-05-31T10:00:00+03:00",
        "event_type": "agent_start",
        "agent": "codex",
    }

    path = append_jsonl_event(root, event)

    assert path == root / "events" / "2026-05-31.jsonl"
    assert list(read_jsonl_events(path)) == [event]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_storage.py -q
```

Expected: FAIL because storage functions do not exist.

- [ ] **Step 3: Implement append/read**

Implement:

- `journal_root()` defaulting to `~/.agent-journal`
- `append_jsonl_event(root, event)`
- `read_jsonl_events(path)`
- atomic line append with newline

- [ ] **Step 4: Run test**

```bash
pytest tests/test_storage.py -q
```

Expected: PASS.

## Chunk 3: Git Context and Evidence

### Task 4: Detect Repository Context

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/git_context.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_git_context.py`

- [ ] **Step 1: Write tests for non-git and git directories**

```python
from agent_journal.git_context import get_git_context


def test_get_git_context_returns_none_outside_repo(tmp_path):
    ctx = get_git_context(tmp_path)
    assert ctx["repo"] is None
    assert ctx["branch"] is None
    assert ctx["commit"] is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_git_context.py -q
```

Expected: FAIL.

- [ ] **Step 3: Implement git context**

Use `subprocess.run` safely with:

- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git status --porcelain`

Return a dict with:

- `repo`
- `branch`
- `commit`
- `dirty`
- `changed_files`

- [ ] **Step 4: Run test**

```bash
pytest tests/test_git_context.py -q
```

Expected: PASS.

### Task 5: Git Post-Commit Hook Event

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/scripts/hooks/post-commit`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/cli.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/tests/test_cli.py`

- [ ] **Step 1: Add CLI test for `event git_commit`**

```python
def test_event_command_accepts_git_commit(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_JOURNAL_HOME", str(tmp_path))
    exit_code = main(["event", "--type", "git_commit", "--agent", "git"])
    assert exit_code == 0
```

- [ ] **Step 2: Implement `agent-journal event`**

Command:

```bash
agent-journal event --type git_commit --agent git
```

It should:

- normalize event
- enrich with git context from cwd
- append to JSONL

- [ ] **Step 3: Add post-commit hook script**

The script should call:

```bash
agent-journal event --type git_commit --agent "${AGENT_JOURNAL_AGENT:-git}"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_cli.py tests/test_git_context.py tests/test_storage.py -q
```

Expected: PASS.

## Chunk 4: Agent Wrappers

### Task 6: Generic Wrapper Script

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/scripts/wrappers/agent-journal-wrapper.sh`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/tests/test_cli.py`

- [ ] **Step 1: Define wrapper behavior**

The wrapper receives:

```bash
AGENT_JOURNAL_AGENT=codex
AGENT_JOURNAL_REAL_BIN=/opt/homebrew/bin/codex
```

It logs:

- `agent_start`
- runs real binary with original args
- captures exit code and duration
- logs `agent_end`
- exits with the real binary exit code

- [ ] **Step 2: Add a shell-level smoke test**

Use a fake binary in a temp directory that exits `7`. Assert the wrapper also exits `7` and writes two events.

- [ ] **Step 3: Implement wrapper**

Implementation requirements:

- no prompt/content logging
- preserve args exactly
- handle missing real binary with clear error
- use `date +%s` for duration

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_cli.py -q
```

Expected: PASS.

### Task 7: Installer for Wrapper Binaries

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/install.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_install.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/cli.py`

- [ ] **Step 1: Write installer tests**

Test that install creates:

```text
~/.agent-journal/bin/codex
~/.agent-journal/bin/claude
~/.agent-journal/bin/gemini
```

Each generated script should point to the detected real binary.

- [ ] **Step 2: Implement `agent-journal install wrappers`**

Command:

```bash
agent-journal install wrappers
```

Behavior:

- detect real binaries with `shutil.which`
- avoid wrapping itself if journal bin is already first on PATH
- create wrapper scripts
- print PATH instruction

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_install.py tests/test_cli.py -q
```

Expected: PASS.

## Chunk 5: Reporting MVP

### Task 8: Aggregate Daily Events

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/report.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_report.py`

- [ ] **Step 1: Write classification tests**

```python
from agent_journal.report import classify_daily_work


def test_commit_with_verification_is_completed_verified():
    items = classify_daily_work([
        {"event_type": "git_commit", "commit": "abc123", "repo": "/repo", "agent": "codex"},
        {
            "event_type": "verification",
            "repo": "/repo",
            "evidence": {"verification_status": "passed"},
        },
    ])

    assert items["completed_verified"]


def test_completion_claim_without_commit_is_claimed():
    items = classify_daily_work([
        {
            "event_type": "task_completed_claim",
            "agent": "gemini",
            "semantic": {"task_id": "TASK-1", "note": "Done"},
        }
    ])

    assert items["completed_claimed"]
```

- [ ] **Step 2: Implement classification**

Group by:

- repo
- agent
- task_id when available
- commit when available

Classify into:

- completed_verified
- completed_claimed
- in_progress
- blocked
- risky

- [ ] **Step 3: Render Markdown report**

Add:

```python
render_markdown_report(date, classified) -> str
```

Required sections:

- Summary
- Completed Verified
- Completed Claimed
- In Progress
- Blocked
- Risky / Needs Review
- Raw Event Count

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_report.py -q
```

Expected: PASS.

### Task 9: `agent-journal report --today`

**Files:**
- Modify: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/cli.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/tests/test_cli.py`

- [ ] **Step 1: Add CLI report test**

Test command:

```bash
agent-journal report --date 2026-05-31
```

Expected:

- reads `events/2026-05-31.jsonl`
- writes `reports/2026-05-31.md`
- prints report path

- [ ] **Step 2: Implement report command**

Options:

- `--today`
- `--date YYYY-MM-DD`
- `--print`
- `--output PATH`

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_cli.py tests/test_report.py -q
```

Expected: PASS.

## Chunk 6: SQLite Storage

### Task 10: Add SQLite WAL Storage

**Files:**
- Modify: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/storage.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/tests/test_storage.py`

- [ ] **Step 1: Write SQLite tests**

Assert:

- database initializes
- WAL mode is enabled
- event insert works
- duplicate `event_id` is ignored or rejected deterministically

- [ ] **Step 2: Implement schema**

Tables:

```sql
CREATE TABLE events (
  event_id TEXT PRIMARY KEY,
  schema_version INTEGER NOT NULL,
  ts TEXT NOT NULL,
  event_type TEXT NOT NULL,
  agent TEXT,
  session_id TEXT,
  cwd TEXT,
  repo TEXT,
  branch TEXT,
  commit_hash TEXT,
  exit_code INTEGER,
  duration_ms INTEGER,
  raw_json TEXT NOT NULL
);

CREATE INDEX idx_events_ts ON events(ts);
CREATE INDEX idx_events_repo ON events(repo);
CREATE INDEX idx_events_agent ON events(agent);
CREATE INDEX idx_events_type ON events(event_type);
```

- [ ] **Step 3: Keep JSONL mirror**

`agent-journal event` writes both:

- SQLite primary store
- JSONL daily mirror

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_storage.py tests/test_cli.py -q
```

Expected: PASS.

## Chunk 7: Privacy and Redaction

### Task 11: Redact Sensitive Values

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/security.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_security.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/events.py`

- [ ] **Step 1: Write redaction tests**

Test redaction for:

- `OPENAI_API_KEY=...`
- `ANTHROPIC_API_KEY=...`
- `GEMINI_API_KEY=...`
- `Authorization: Bearer ...`
- long token-like strings

- [ ] **Step 2: Implement conservative redaction**

Function:

```python
redact_value(value: object) -> object
```

Rules:

- recurse through dict/list/string
- redact known secret key names
- redact bearer tokens
- do not log full command args by default

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_security.py tests/test_events.py -q
```

Expected: PASS.

## Chunk 8: MCP Semantic Layer

### Task 12: MCP Server with Semantic Tools

**Files:**
- Create: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/mcp_server.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/tests/test_mcp_server.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/pyproject.toml`

- [ ] **Step 1: Add MCP dependency**

Add the Python MCP SDK dependency after checking the current recommended package name/version.

- [ ] **Step 2: Implement tools**

Tools:

- `journal_note`
- `journal_task_completed`
- `journal_task_blocked`
- `journal_daily_report`

Each write event(s) through the same storage path.

- [ ] **Step 3: Keep MCP responses tiny**

Expected tool response:

```text
logged
```

or:

```text
report: /Users/varienos/.agent-journal/reports/2026-05-31.md
```

- [ ] **Step 4: Add tests**

Test tool handlers directly without launching a full MCP client if possible.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_mcp_server.py tests/test_storage.py -q
```

Expected: PASS.

## Chunk 9: Install and Operations

### Task 13: Installer for Git Hook and MCP Config Snippets

**Files:**
- Modify: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/install.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/tests/test_install.py`
- Create: `/Users/varienos/Landing/Repo/agent-journal/docs/operations.md`

- [ ] **Step 1: Implement `agent-journal install git-hook`**

Preferred MVP:

- print instructions for adding global git hook template
- optionally install into a chosen repo with `--repo PATH`

Do not overwrite existing hooks without backup.

- [ ] **Step 2: Implement `agent-journal install mcp-snippets`**

Print config snippets for:

- Codex
- Claude Code
- Gemini CLI

The command should not mutate user global configs in MVP unless `--write` is explicitly passed.

- [ ] **Step 3: Write operations doc**

Cover:

- PATH setup for wrappers
- git hook setup
- MCP setup
- daily report cron/Codex automation examples
- troubleshooting missing events

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_install.py -q
```

Expected: PASS.

## Chunk 10: Daily Automation

### Task 14: Report Automation Script

**Files:**
- Modify: `/Users/varienos/Landing/Repo/agent-journal/docs/operations.md`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/src/agent_journal/cli.py`
- Modify: `/Users/varienos/Landing/Repo/agent-journal/tests/test_cli.py`

- [ ] **Step 1: Add `report --today --write` behavior**

Ensure:

```bash
agent-journal report --today
```

writes:

```text
~/.agent-journal/reports/YYYY-MM-DD.md
```

- [ ] **Step 2: Document cron example**

```bash
0 23 * * * /Users/varienos/.agent-journal/bin/agent-journal report --today
```

- [ ] **Step 3: Document Codex automation prompt**

Suggested prompt:

```text
Generate today's Agent Journal report by running `agent-journal report --today`.
Summarize completed_verified, completed_claimed, in_progress, blocked, and risky items.
Do not modify project files.
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_cli.py tests/test_report.py -q
```

Expected: PASS.

## Verification Plan

Run full test suite:

```bash
pytest -q
```

Manual smoke test:

```bash
agent-journal event --type agent_start --agent codex
agent-journal event --type task_completed_claim --agent codex --task TASK-1 --note "Smoke test completed"
agent-journal report --today --print
```

Expected:

- event JSONL exists under `~/.agent-journal/events/`
- SQLite DB exists under `~/.agent-journal/agent-journal.db`
- report contains `completed_claimed`

Wrapper smoke test:

```bash
export PATH="$HOME/.agent-journal/bin:$PATH"
codex --help
agent-journal report --today --print
```

Expected:

- `agent_start` and `agent_end` events for `codex`
- real `codex --help` behavior is preserved

Git hook smoke test:

```bash
git commit --allow-empty -m "test: agent journal hook"
agent-journal report --today --print
```

Expected:

- `git_commit` event appears
- commit hash appears in report

## Definition of Done for MVP

- `agent-journal event` writes normalized events.
- JSONL daily mirror works.
- SQLite WAL storage works.
- `codex`, `claude`, and `gemini` wrappers can log start/end without changing CLI exit behavior.
- git post-commit hook can log commit metadata.
- `agent-journal report --today` produces Markdown.
- Completion claims without evidence are not marked verified.
- Sensitive values are redacted.
- Installation docs explain wrapper, hook, MCP, and automation setup.

## Out of Scope for MVP

- Cloud dashboard.
- Web UI.
- Full prompt transcript logging.
- File content logging.
- Team/multi-user sync.
- Automatic task inference from natural language.
- Perfect cross-agent session reconstruction.

## Open Questions

- Should `agent-journal install` mutate global Codex/Claude/Gemini MCP configs automatically, or only print snippets?
- Should reports be purely deterministic, or should an optional LLM summarizer rewrite them into executive prose?
- Should `completed_verified` require a commit, or can a passing verification command plus no diff count as verified for non-code tasks?
- Should this integrate with Backlog.md task IDs in a later phase?

