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

Correlation rules:

- `commit` is the strongest verification key. A `git_commit` item is
  `completed_verified` only when a passed `verification` event has the same
  commit hash.
- `session_id` links events emitted by the same agent process or MCP session.
  A `task_completed_claim` can become `completed_verified` when a passed
  `verification` event has the same `session_id` and a compatible `repo`.
- `semantic.task_id` links explicit task claims to explicit verification
  evidence. A `task_completed_claim` can become `completed_verified` when a
  passed `verification` event has the same `semantic.task_id` and a compatible
  `repo`.
- Repos are compatible when both events have the same `repo`, or when one side
  was produced by a legacy/MCP writer that did not include repo metadata.
- If no matching passed verification exists, task completion remains
  `completed_claimed` and commit work remains `in_progress`.
- Failed verification events are reported as risky and do not verify matching
  tasks or commits.

Privacy rules:

- Do not log prompt transcripts by default.
- Do not log full file contents.
- Redact known API keys, bearer tokens, passwords, and secret-looking values.
