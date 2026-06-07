# Contributing

Thanks for helping improve Agentic Journal.

## Project Scope

Agentic Journal is a local-first, observer-first activity journal for AI coding
agents. Contributions should preserve these boundaries:

- Do not capture full prompt transcripts by default.
- Do not log secrets, full file contents, or sensitive tool payloads.
- Keep verified work distinct from claimed work.
- Prefer small, testable changes over broad rewrites.

## Development

Set up the repo:

```bash
uv sync --dev
```

Run the core checks:

```bash
uv run pytest -q
scripts/verify.sh
scripts/package-smoke.sh
```

## Pull Requests

Before opening a pull request:

- Add or update focused tests for behavior changes.
- Update `README.md` or `docs/` when user-facing setup changes.
- Keep commits scoped and explain the user-visible impact.
- Confirm the package smoke script still passes for install-related changes.
