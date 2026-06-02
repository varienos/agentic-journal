import importlib.util
from pathlib import Path


def _load_release_tools():
    spec = importlib.util.spec_from_file_location("release_tools", Path("scripts/release_tools.py"))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_release_check_validates_project_version_tag_and_changelog(tmp_path):
    tools = _load_release_tools()
    root = tmp_path
    (root / "src" / "agent_journal").mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    (root / "src" / "agent_journal" / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        "## [1.2.3] - 2026-06-02\n"
        "### Added\n"
        "- Release automation.\n",
        encoding="utf-8",
    )

    result = tools.check_release(root, tag="v1.2.3")

    assert result.version == "1.2.3"
    assert result.tag == "v1.2.3"
    assert result.changelog_section.startswith("### Added")


def test_release_check_rejects_version_mismatches(tmp_path):
    tools = _load_release_tools()
    root = tmp_path
    (root / "src" / "agent_journal").mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    (root / "src" / "agent_journal" / "__init__.py").write_text('__version__ = "1.2.4"\n', encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] - 2026-06-02\n- Notes.\n",
        encoding="utf-8",
    )

    try:
        tools.check_release(root, tag="v1.2.3")
    except tools.ReleaseError as exc:
        assert "__version__" in str(exc)
    else:
        raise AssertionError("expected version mismatch to fail")


def test_changelog_notes_extracts_only_requested_version(tmp_path):
    tools = _load_release_tools()
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n"
        "## [Unreleased]\n"
        "- Future work.\n\n"
        "## [1.2.3] - 2026-06-02\n"
        "### Added\n"
        "- Target notes.\n\n"
        "## [1.2.2] - 2026-05-31\n"
        "- Older notes.\n",
        encoding="utf-8",
    )

    notes = tools.extract_changelog_section(changelog, "1.2.3")

    assert "Target notes" in notes
    assert "Future work" not in notes
    assert "Older notes" not in notes


def test_release_tools_cli_writes_notes_file(tmp_path):
    tools = _load_release_tools()
    root = tmp_path
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] - 2026-06-02\n- Notes.\n",
        encoding="utf-8",
    )
    output = tmp_path / "notes.md"

    exit_code = tools.main(["notes", "--root", str(root), "--version", "1.2.3", "--output", str(output)])

    assert exit_code == 0
    assert output.read_text(encoding="utf-8") == "- Notes.\n"
