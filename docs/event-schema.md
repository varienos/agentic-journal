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

Privacy rules:

- Do not log prompt transcripts by default.
- Do not log full file contents.
- Redact known API keys, bearer tokens, passwords, and secret-looking values.

