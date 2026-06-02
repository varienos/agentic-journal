from pathlib import Path


def test_release_workflow_creates_github_release_from_version_tags():
    workflow = Path(".github/workflows/release.yml")

    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "tags:" in text
    assert "v*.*.*" in text
    assert "contents: write" in text
    assert "scripts/release-check.sh --tag" in text
    assert "scripts/release_tools.py notes" in text
    assert "uv build --wheel --sdist" in text
    assert "gh release create" in text
    assert "--verify-tag" in text


def test_release_check_script_delegates_to_python_tool():
    script = Path("scripts/release-check.sh")

    assert script.exists()
    text = script.read_text(encoding="utf-8")
    assert "scripts/release_tools.py" in text
    assert "check" in text


def test_changelog_has_unreleased_and_current_version_sections():
    changelog = Path("CHANGELOG.md")

    assert changelog.exists()
    text = changelog.read_text(encoding="utf-8")
    assert "# Changelog" in text
    assert "## [Unreleased]" in text
    assert "## [0.1.0] - 2026-06-02" in text


def test_readme_and_operations_document_release_flow():
    readme = Path("README.md").read_text(encoding="utf-8")
    operations = Path("docs/operations.md").read_text(encoding="utf-8")

    assert "CHANGELOG.md" in readme
    assert "Release" in readme
    assert "scripts/release-check.sh" in operations
    assert 'git tag "v$VERSION"' in operations
    assert 'git push origin "v$VERSION"' in operations
    assert "gh release" in operations
