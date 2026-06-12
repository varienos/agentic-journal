from __future__ import annotations

from pathlib import Path

from agentic_journal.project_config import (
    discover_project_mirror_configs,
    event_matches_project,
    load_project_config,
)


def test_project_config_resolves_relative_project_and_mirror_paths(tmp_path):
    project = tmp_path / "cortex"
    project.mkdir()
    config_path = project / ".agentic-journal.toml"
    config_path.write_text(
        "\n".join(
            [
                "[project]",
                'id = "cortex"',
                'path = "."',
                "",
                "[mirror]",
                "enabled = true",
                'path = "Agentbase/.agentic-journal"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    config = load_project_config(config_path)

    assert config.project_id == "cortex"
    assert config.project_path == project.resolve()
    assert config.mirror_enabled is True
    assert config.mirror_root == project.resolve() / "Agentbase" / ".agentic-journal"


def test_project_config_defaults_mirror_to_enabled(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    config_path = project / ".agentic-journal.toml"
    config_path.write_text(
        "\n".join(
            [
                "[project]",
                'path = "."',
                "",
                "[mirror]",
                'path = ".agentic-journal"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert load_project_config(config_path).mirror_enabled is True


def test_event_matches_project_exact_child_and_non_matching_paths(tmp_path):
    project = tmp_path / "cortex"
    project.mkdir()
    config_path = project / ".agentic-journal.toml"
    config_path.write_text(
        "\n".join(
            [
                "[project]",
                'path = "."',
                "",
                "[mirror]",
                'path = "Agentbase/.agentic-journal"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    config = load_project_config(config_path)

    assert event_matches_project(config, {"cwd": str(project)})
    assert event_matches_project(config, {"repo": str(project / "Codebase" / "Cortex")})
    assert event_matches_project(config, {"cwd": str(project / "Agentbase")})
    assert not event_matches_project(config, {"cwd": str(tmp_path / "cortex-neon")})
    assert not event_matches_project(config, {"cwd": str(tmp_path / "other")})


def test_disabled_mirror_config_does_not_match(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    config_path = project / ".agentic-journal.toml"
    config_path.write_text(
        "\n".join(
            [
                "[project]",
                'path = "."',
                "",
                "[mirror]",
                "enabled = false",
                'path = ".agentic-journal"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    config = load_project_config(config_path)

    assert config.mirror_enabled is False
    assert not event_matches_project(config, {"cwd": str(project)})


def test_discover_project_mirror_configs_from_cwd_and_repo_dedupes(tmp_path):
    project = tmp_path / "cortex"
    agentbase = project / "Agentbase"
    codebase = project / "Codebase" / "Cortex"
    agentbase.mkdir(parents=True)
    codebase.mkdir(parents=True)
    config_path = project / ".agentic-journal.toml"
    config_path.write_text(
        "\n".join(
            [
                "[project]",
                'id = "cortex"',
                'path = "."',
                "",
                "[mirror]",
                'path = "Agentbase/.agentic-journal"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    configs = discover_project_mirror_configs(
        {
            "cwd": str(codebase),
            "repo": str(codebase),
        }
    )

    assert [config.config_path for config in configs] == [config_path.resolve()]
    assert configs[0].mirror_root == agentbase.resolve() / ".agentic-journal"


def test_discover_project_mirror_configs_ignores_invalid_config(tmp_path, capsys):
    project = tmp_path / "project"
    child = project / "child"
    child.mkdir(parents=True)
    (project / ".agentic-journal.toml").write_text("[project]\n", encoding="utf-8")

    assert discover_project_mirror_configs({"cwd": str(child)}) == []
    assert "invalid Agentic Journal project config" in capsys.readouterr().err
