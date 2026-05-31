from __future__ import annotations

import os
from pathlib import Path

DEFAULT_CONFIG = """# Agent Journal local configuration
[journal]
schema_version = 1
jsonl_mirror = true
sqlite_wal = true

[privacy]
log_prompts = false
log_file_contents = false
redact_secrets = true
"""


def journal_root() -> Path:
    configured = os.environ.get("AGENT_JOURNAL_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".agent-journal"


def ensure_config(root: str | Path | None = None) -> Path:
    root_path = Path(root).expanduser() if root else journal_root()
    root_path.mkdir(parents=True, exist_ok=True)
    config_path = root_path / "config.toml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return config_path
