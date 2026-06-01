#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

VENV="$TMP_ROOT/venv"
PYTHON="$VENV/bin/python"
JOURNAL_HOME="$TMP_ROOT/journal"

cd "$ROOT"

uv build --wheel --out-dir "$TMP_ROOT/dist" >/dev/null
python3 -m venv "$VENV"
"$PYTHON" -m pip install --no-cache-dir --upgrade pip >/dev/null
"$PYTHON" -m pip install --no-cache-dir "$TMP_ROOT"/dist/*.whl >/dev/null

AGENT_JOURNAL_HOME="$JOURNAL_HOME" "$VENV/bin/agent-journal" --help >/dev/null
AGENT_JOURNAL_HOME="$JOURNAL_HOME" "$VENV/bin/agent-journal" web --help >/dev/null
AGENT_JOURNAL_HOME="$JOURNAL_HOME" "$VENV/bin/agent-journal" event --type agent_start --agent codex --session-id PACKAGE-MISSING >/dev/null
AGENT_JOURNAL_HOME="$JOURNAL_HOME" "$VENV/bin/agent-journal" guard session-end --agent codex --session-id PACKAGE-MISSING >/dev/null
test -x "$VENV/bin/agent-journal-mcp"

"$PYTHON" - <<PY
from agent_journal.web import build_events_payload, render_dashboard_html

payload = build_events_payload("$JOURNAL_HOME", "$(date +%F)")
assert payload["summary"]["risky"] == 1
assert "Agent Journal Live" in render_dashboard_html()
PY

"$PYTHON" - <<'PY'
from agent_journal.mcp_server import create_mcp_server

server = create_mcp_server()
expected = {
    "journal_note",
    "journal_task_completed",
    "journal_task_blocked",
    "journal_daily_report",
}
assert expected.issubset(set(server._tool_manager._tools))
PY

mkdir -p "$TMP_ROOT/hook-repo"
git -C "$TMP_ROOT/hook-repo" init >/dev/null
AGENT_JOURNAL_HOME="$TMP_ROOT/hook-journal" \
  "$VENV/bin/agent-journal" install git-hook --repo "$TMP_ROOT/hook-repo" >"$TMP_ROOT/install-git-hook.out"
test -x "$TMP_ROOT/hook-repo/.git/hooks/post-commit"
grep -q "agent-journal event --type git_commit" "$TMP_ROOT/hook-repo/.git/hooks/post-commit"

mkdir -p "$TMP_ROOT/real"
cat > "$TMP_ROOT/real/codex" <<'SH'
#!/usr/bin/env sh
exit 7
SH
chmod +x "$TMP_ROOT/real/codex"

PATH="$TMP_ROOT/real:$VENV/bin:$PATH" \
  AGENT_JOURNAL_HOME="$JOURNAL_HOME" \
  "$VENV/bin/agent-journal" install wrappers >"$TMP_ROOT/install-wrappers.out"
test -x "$JOURNAL_HOME/bin/codex"

if grep -q "scripts/wrappers" "$JOURNAL_HOME/bin/codex"; then
  echo "generated wrapper unexpectedly depends on scripts/wrappers" >&2
  exit 1
fi

set +e
PATH="$VENV/bin:$PATH" AGENT_JOURNAL_HOME="$JOURNAL_HOME" "$JOURNAL_HOME/bin/codex"
WRAPPER_STATUS=$?
set -e
test "$WRAPPER_STATUS" -eq 7

"$PYTHON" - <<PY
from pathlib import Path
import glob
import json

paths = glob.glob("$JOURNAL_HOME/events/*.jsonl")
assert paths, "packaged wrapper did not write JSONL events"
events = [json.loads(line) for line in Path(paths[0]).read_text().splitlines()]
wrapper_events = [event for event in events if event.get("command") == "codex"]
assert [event["event_type"] for event in wrapper_events] == ["agent_start", "agent_end"]
assert wrapper_events[-1]["exit_code"] == 7
assert any(
    event["event_type"] == "verification"
    and event.get("agent") == "codex"
    and (event.get("semantic") or {}).get("status") == "journal_missing"
    for event in events
)
PY

set +e
PATH="/usr/bin:/bin" AGENT_JOURNAL_HOME="$TMP_ROOT/missing-path-journal" \
  "$JOURNAL_HOME/bin/codex" 2>"$TMP_ROOT/missing-path.err"
MISSING_PATH_STATUS=$?
set -e
test "$MISSING_PATH_STATUS" -eq 7
grep -q "agent-journal command not found" "$TMP_ROOT/missing-path.err"

echo "agent-journal package smoke passed"
