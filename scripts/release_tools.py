#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple, Sequence


VERSION_RE = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
CHANGELOG_HEADING_RE = re.compile(r"^## \[([^\]]+)\](?: - \d{4}-\d{2}-\d{2})?\s*$")


class ReleaseError(RuntimeError):
    pass


class ReleaseCheckResult(NamedTuple):
    version: str
    tag: str | None
    changelog_section: str


def read_pyproject_version(root: str | Path) -> str:
    pyproject = Path(root) / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def read_package_version(root: str | Path) -> str:
    init_file = Path(root) / "src" / "agent_journal" / "__init__.py"
    match = VERSION_RE.search(init_file.read_text(encoding="utf-8"))
    if not match:
        raise ReleaseError("__version__ is missing from src/agent_journal/__init__.py")
    return match.group(1)


def extract_changelog_section(changelog: str | Path, version: str) -> str:
    path = Path(changelog)
    lines = path.read_text(encoding="utf-8").splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        match = CHANGELOG_HEADING_RE.match(line)
        if match and match.group(1) == version:
            start = index + 1
            break
    if start is None:
        raise ReleaseError(f"CHANGELOG.md is missing a section for [{version}]")

    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## ["):
            end = index
            break

    section = "\n".join(lines[start:end]).strip()
    if not section:
        raise ReleaseError(f"CHANGELOG.md section [{version}] is empty")
    return section + "\n"


def check_release(root: str | Path, tag: str | None = None) -> ReleaseCheckResult:
    root_path = Path(root)
    pyproject_version = read_pyproject_version(root_path)
    package_version = read_package_version(root_path)
    if pyproject_version != package_version:
        raise ReleaseError(
            "pyproject.toml version "
            f"({pyproject_version}) does not match __version__ ({package_version})"
        )
    if not SEMVER_RE.match(pyproject_version):
        raise ReleaseError(f"version is not SemVer-like: {pyproject_version}")
    if tag and tag != f"v{pyproject_version}":
        raise ReleaseError(f"tag {tag} does not match project version v{pyproject_version}")

    changelog = root_path / "CHANGELOG.md"
    changelog_text = changelog.read_text(encoding="utf-8")
    if "## [Unreleased]" not in changelog_text:
        raise ReleaseError("CHANGELOG.md is missing an [Unreleased] section")
    section = extract_changelog_section(changelog, pyproject_version)
    return ReleaseCheckResult(version=pyproject_version, tag=tag, changelog_section=section)


def _add_check_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("check", help="Validate release version, tag, and changelog state")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--tag")


def _add_notes_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("notes", help="Extract changelog notes for a release version")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version", required=True)
    parser.add_argument("--output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="release_tools.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_check_parser(subparsers)
    _add_notes_parser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check":
            result = check_release(args.root, tag=args.tag)
            tag = result.tag or f"v{result.version}"
            print(f"release check passed for {tag}")
            return 0
        if args.command == "notes":
            notes = extract_changelog_section(Path(args.root) / "CHANGELOG.md", args.version)
            if args.output:
                Path(args.output).write_text(notes, encoding="utf-8")
            else:
                print(notes, end="")
            return 0
    except ReleaseError as exc:
        print(f"release check failed: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
