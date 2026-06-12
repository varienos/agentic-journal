# Agentic Journal Event Schema

Agentic Journal stores append-only events. Events are mirrored to daily JSONL files
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
  `verification` event has the same `session_id` and a compatible `repo`;
  matching `session_id` is accepted only when task ids do not conflict.
- MCP tools inherit `AGENTIC_JOURNAL_SESSION_ID` and git context from the MCP
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
- `agentic-journal guard session-end` writes a failed `verification` event with
  `semantic.status = "journal_missing"` when a session ends without a
  `session_summary`, `task_completed_claim`, or `task_blocked` event. Generic
  `semantic_note` entries do not satisfy the session outcome requirement.
- Guard fallback events include `files_changed` from git status when available.
  This gives objective context for missing summaries without storing prompt
  transcripts or inventing completed work.
- Duplicate `event_id` writes are ignored so SQLite and the daily JSONL files
  remain aligned.
- SQLite stores the complete event payload in `raw_json`; `raw_json` is the source of truth.
  denormalized index columns such as `ts`, `repo`, `agent`, `event_type`, and
  `session_id` are query accelerators that can be rebuilt from `raw_json`.
- Events with a future `schema_version` are skipped by current readers instead
  of being silently misclassified.

Project mirror rules:

- A `.agentic-journal.toml` file can opt a project into a local mirror. Matching
  is based on exact or child-path matches against the event `repo` or `cwd`.
- Mirror roots use the same event schema, SQLite table, daily JSONL layout, and
  idempotent `event_id` behavior as the global journal.
- Mirror writes preserve the original event payload. They do not add
  project-specific fields or rewrite paths.
- Global journal writes remain primary. A mirror write failure is reported to
  stderr and does not fail the global write.
- Readers can point `status`, `report`, or `web` at a mirror root with `--root`
  and receive the same report or API payload shape as the global journal.

Privacy rules:

- Do not log prompt transcripts by default.
- Do not log full file contents.
- Redact known API keys, bearer tokens, passwords, URL credentials, PEM private
  keys, and secret-looking values in both structured fields and free text.
- Journal directories and files are owner-only by default: directories are
  written with `0700`, files and SQLite/WAL sidecars with `0600`.
- Project mirrors contain the same sensitive summaries, notes, paths, branch
  names, commit hashes, and evidence metadata as the global journal. Keep mirror
  directories out of git and mount them only into trusted containers.
- Free-text semantic fields are capped by `MAX_SEMANTIC_TEXT`; oversized
  `summary`, `note`, and `reason` values are truncated with `…[truncated]`.
