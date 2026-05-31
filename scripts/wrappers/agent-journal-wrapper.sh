#!/usr/bin/env sh
set -u

if [ -z "${AGENT_JOURNAL_REAL_BIN:-}" ]; then
  echo "AGENT_JOURNAL_REAL_BIN is required" >&2
  exit 127
fi

if [ ! -x "$AGENT_JOURNAL_REAL_BIN" ]; then
  echo "real agent binary is not executable: $AGENT_JOURNAL_REAL_BIN" >&2
  exit 127
fi

AGENT="${AGENT_JOURNAL_AGENT:-unknown}"
SESSION_ID="$(date +%s)-$$"
START_TS="$(date +%s)"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"

journal_event() {
  if command -v agent-journal >/dev/null 2>&1; then
    agent-journal event "$@"
  else
    PYTHONPATH="$PROJECT_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 -m agent_journal.cli event "$@"
  fi
}

journal_event --type agent_start --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT" >/dev/null 2>&1 || true

"$AGENT_JOURNAL_REAL_BIN" "$@"
STATUS=$?

END_TS="$(date +%s)"
DURATION_MS=$(( (END_TS - START_TS) * 1000 ))

journal_event --type agent_end --agent "$AGENT" --session-id "$SESSION_ID" --command "$AGENT" --exit-code "$STATUS" --duration-ms "$DURATION_MS" >/dev/null 2>&1 || true

exit "$STATUS"
