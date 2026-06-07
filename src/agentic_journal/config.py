from __future__ import annotations

import os
from pathlib import Path

from agentic_journal.events import SCHEMA_VERSION

DEFAULT_CONFIG = f"""# Agentic Journal local configuration
[journal]
schema_version = {SCHEMA_VERSION}
jsonl_mirror = true
sqlite_wal = true

[privacy]
log_prompts = false
log_file_contents = false
redact_secrets = true
"""

# Journal data (events, summaries, possibly secret-bearing free text) is
# sensitive and must not be world-readable on shared hosts.
DIR_MODE = 0o700
FILE_MODE = 0o600


def secure_dir(path: str | Path) -> Path:
    """Create ``path`` (and parents) and restrict it to the owner."""
    dir_path = Path(path).expanduser()
    dir_path.mkdir(parents=True, exist_ok=True)
    try:
        dir_path.chmod(DIR_MODE)
    except OSError:
        pass
    return dir_path


def secure_file(path: str | Path) -> Path:
    """Restrict an already-created file to the owner (best-effort)."""
    file_path = Path(path).expanduser()
    try:
        file_path.chmod(FILE_MODE)
    except OSError:
        pass
    return file_path


def journal_root() -> Path:
    configured = os.environ.get("AGENTIC_JOURNAL_HOME") or os.environ.get("AGENT_JOURNAL_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / ".agentic-journal"


def ensure_config(root: str | Path | None = None) -> Path:
    root_path = secure_dir(root if root is not None else journal_root())
    config_path = root_path / "config.toml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
        secure_file(config_path)
    return config_path
