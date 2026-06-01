# Agent Journal Event Schema

Agent Journal stores append-only events. Events are mirrored to daily JSONL files
and inserted into SQLite.

Required fields:

- `schema_version`
- `event_id`
- `ts`
- `event_type`

Common optional fields:

- `agent`
- `session_id`
- `cwd`
- `repo`
- `branch`
- `commit`
- `command`
- `exit_code`
- `duration_ms`
- `files_changed`
- `semantic`
- `evidence`

Outcome events:

- `session_summary` is the preferred end-of-session semantic event for daily
  reporting.
- `semantic.summary` should be a concise human-readable description of what the
  agent did.
- `semantic.outcome` should be one of `completed`, `in_progress`, `blocked`,
  `no_work`, or `unknown`.
- `semantic.task_id` should be set when the session maps to a Backlog task or
  other stable task identifier.

Correlation rules:

- `commit` is the strongest verification key. A `git_commit` item is
  `completed_verified` only when a passed `verification` event has the same
  commit hash.
- `session_id` links events emitted by the same agent process or MCP session.
  A `task_completed_claim` can become `completed_verified` when a passed
  `verification` event has the same `session_id` and a compatible `repo`.
- MCP tools inherit `AGENT_JOURNAL_SESSION_ID` and git context from the MCP
  server process. This lets `journal_task_completed`, `journal_task_blocked`,
  and `journal_session_summary` correlate with wrapper session lifecycle events.
- `semantic.task_id` links explicit task claims to explicit verification
  evidence. A `task_completed_claim` can become `completed_verified` when a
  passed `verification` event has the same `semantic.task_id` and a compatible
  `repo`.
- New writers should put task ids in `semantic.task_id`. Readers also accept a
  top-level `task_id` as a legacy fallback for older or external event writers.
- Repos are compatible when both events have the same `repo`, or when one side
  was produced by a legacy/MCP writer that did not include repo metadata.
- If no matching passed verification exists, task completion remains
  `completed_claimed` and commit work remains `in_progress`.
- Failed verification events are reported as risky and do not verify matching
  tasks or commits.
- `agent-journal guard session-end` writes a failed `verification` event with
  `semantic.status = "journal_missing"` when a session ends without a
  `session_summary`, `task_completed_claim`, or `task_blocked` event. Generic
  `semantic_note` entries do not satisfy the session outcome requirement.
- Duplicate `event_id` writes are ignored so SQLite and the daily JSONL mirror
  remain aligned.

Privacy rules:

- Do not log prompt transcripts by default.
- Do not log full file contents.
- Redact known API keys, bearer tokens, passwords, and secret-looking values.
