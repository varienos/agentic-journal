# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses `vMAJOR.MINOR.PATCH` Git tags for GitHub releases.

## [Unreleased]

## [0.1.0] - 2026-06-02

### Added

- Local `agent-journal` CLI for append-only AI agent activity events.
- `agent-journal-mcp` server with semantic note, session summary, completed, blocked, and daily report tools.
- Codex, Claude, and Gemini wrapper installer with session start/end capture and missing-summary guard.
- Daily Markdown reports with verified, claimed, observed, blocked, notes, and risky evidence buckets.
- Live local web dashboard with provider coverage and missing-summary diagnosis.
- `agent-journal doctor` setup audit for wrappers, MCP config hints, instructions, hooks, token mode, and provider coverage.
- Git post-commit hook installer that records commit metadata and changed files.
- Native hook guidance for Claude SessionEnd, Gemini hooks, and Codex automation.
- GitHub CI, package smoke checks, release metadata checks, and tag-driven GitHub release automation.
