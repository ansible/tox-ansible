"""Unit tests for molecule test type support."""

from __future__ import annotations

import contextlib
import io
import os

from pathlib import Path
from typing import TYPE_CHECKING

import pytest  # noqa: TC002

from tox.config.cli.parse import Options
from tox.config.cli.parser import Parsed
from tox.config.main import Config
from tox.config.source import discover_source
from tox.report import ToxHandler
from tox.session.state import State

from tox_ansible.plugin import (
    Collection,
    _should_include_molecule,
    add_ansible_matrix,
    conf_commands,
    conf_commands_for_molecule,
    conf_commands_pre,
    conf_deps,
    discover_integration_tests,
    discover_molecule_scenarios,
)


if TYPE_CHECKING:
    from collections.abc import Generator


@contextlib.contextmanager
def working_directory(path: Path) -> Generator[None, None, None]:
    """Changes working directory and returns to previous on exit.

    Args:
        path: Path object.
    """
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def test_conf_commands_molecule() -> None:
    """Test default molecule command generation."""
    result = conf_commands_for_molecule(pos_args=None)
    assert len(result) == 1
    assert result[0] == "python3 -m molecule test --all"


def test_conf_commands_molecule_with_args() -> None:
    """Test molecule command generation with pos_args."""
    result = conf_commands_for_molecule(pos_args=("--verbose", "-x"))
    assert len(result) == 1
    assert result[0] == "python3 -m molecule test --all --verbose -x"


def test_conf_commands_molecule_append() -> None:
    """Test molecule_append adds argv after the default command."""
    result = conf_commands_for_molecule(
        pos_args=None,
        molecule_append=["--workers", "4"],
    )
    assert result == ["python3 -m molecule test --all --workers 4"]


def test_conf_commands_molecule_append_and_pos_args() -> None:
    """Test molecule_append and tox pos_args are both applied."""
    result = conf_commands_for_molecule(
        pos_args=("--shared-state",),
        molecule_append=["--workers", "2"],
    )
    assert result == ["python3 -m molecule test --all --workers 2 --shared-state"]


def test_conf_commands_molecule_custom() -> None:
    """Test molecule command generation with custom molecule_commands."""
    custom = ["molecule test -s default", "molecule verify"]
    result = conf_commands_for_molecule(pos_args=None, molecule_commands=custom)
    assert result == custom


def test_conf_commands_molecule_custom_ignores_append_and_pos_args() -> None:
    """Test that molecule_commands fully replaces default/append/pos_args."""
    custom = ["molecule test"]
    result = conf_commands_for_molecule(
        pos_args=("--verbose",),
        molecule_commands=custom,
        molecule_append=["--workers", "4"],
    )
    assert result == custom


def test_conf_commands_molecule_via_conf_commands(tmp_path: Path) -> None:
    """Test molecule commands through the conf_commands dispatcher.

    Args:
        tmp_path: Pytest fixture.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
        extra_envs=[],
    ).get_env("molecule-py3.14-2.20")

    result = conf_commands(
        env_conf=conf,
        collection=Collection(name="test", namespace="test", version="1.0.0"),
        test_type="molecule",
        pos_args=None,
    )
    assert result == ["python3 -m molecule test --all"]


def test_conf_deps_molecule(tmp_path: Path) -> None:
    """Test the conf_deps function for molecule tests.

    Args:
        tmp_path: Pytest fixture.
    """
    with working_directory(tmp_path):
        result = conf_deps(test_type="molecule")
        assert "ansible-dev-environment>=26.2.0" in result
        assert "molecule>=26.4.0" in result
        assert "pytest" in result


def test_commands_pre_molecule(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test pre-command generation for molecule uses editable ade install.

    Args:
        monkeypatch: Pytest fixture.
        tmp_path: Pytest fixture.
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
        extra_envs=[],
    ).get_env("molecule-py3.14-2.20")

    conf.add_config(
        keys=["env_dir", "envdir"],
        of_type=Path,
        default=tmp_path,
        desc="",
    )

    result = conf_commands_pre(
        env_conf=conf,
        collection=Collection(name="test", namespace="test", version="1.0.0"),
        test_type="molecule",
        ansible_version="2.20",
    )
    assert len(result) == 1
    assert "ade install -e" in result[0]
    assert "--acv stable-2.20 --no-seed" in result[0]


def test_discover_molecule_scenarios_found(tmp_path: Path) -> None:
    """Test molecule discovery when scenarios exist.

    Args:
        tmp_path: Pytest fixture.
    """
    scenario_dir = tmp_path / "extensions" / "molecule" / "default"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "molecule.yml").write_text("---\ndriver:\n  name: delegated\n")
    assert discover_molecule_scenarios(tmp_path) is True


def test_discover_molecule_scenarios_not_found(tmp_path: Path) -> None:
    """Test molecule discovery when no scenarios exist.

    Args:
        tmp_path: Pytest fixture.
    """
    assert discover_molecule_scenarios(tmp_path) is False


def test_discover_molecule_scenarios_empty_dir(tmp_path: Path) -> None:
    """Test molecule discovery with extensions/molecule/ but no scenario dirs.

    Args:
        tmp_path: Pytest fixture.
    """
    molecule_dir = tmp_path / "extensions" / "molecule"
    molecule_dir.mkdir(parents=True)
    assert discover_molecule_scenarios(tmp_path) is False


def test_discover_molecule_scenarios_no_molecule_yml(tmp_path: Path) -> None:
    """Test molecule discovery when scenario dir exists but lacks molecule.yml.

    Args:
        tmp_path: Pytest fixture.
    """
    scenario_dir = tmp_path / "extensions" / "molecule" / "default"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "converge.yml").write_text("---\n")
    assert discover_molecule_scenarios(tmp_path) is False


def test_should_include_molecule_true(tmp_path: Path) -> None:
    """Test _should_include_molecule with explicit true.

    Args:
        tmp_path: Pytest fixture.
    """
    assert _should_include_molecule("true", tmp_path) is True


def test_should_include_molecule_false(tmp_path: Path) -> None:
    """Test _should_include_molecule with explicit false.

    Args:
        tmp_path: Pytest fixture.
    """
    scenario_dir = tmp_path / "extensions" / "molecule" / "default"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "molecule.yml").touch()
    assert _should_include_molecule("false", tmp_path) is False


def test_should_include_molecule_auto_with_scenarios(tmp_path: Path) -> None:
    """Test _should_include_molecule auto-discovers scenarios.

    Args:
        tmp_path: Pytest fixture.
    """
    scenario_dir = tmp_path / "extensions" / "molecule" / "default"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "molecule.yml").touch()
    assert _should_include_molecule("auto", tmp_path) is True


def test_should_include_molecule_auto_without_scenarios(tmp_path: Path) -> None:
    """Test _should_include_molecule returns false when no scenarios.

    Args:
        tmp_path: Pytest fixture.
    """
    assert _should_include_molecule("auto", tmp_path) is False


def test_add_ansible_matrix_molecule_auto_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test molecule envs included when scenarios are discovered.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    ini_file = tmp_path / "tox-ansible.ini"
    ini_file.write_text("[ansible]\n")
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    scenario_dir = tmp_path / "extensions" / "molecule" / "default"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "molecule.yml").touch()
    monkeypatch.chdir(tmp_path)
    source = discover_source(ini_file, None)
    parsed = Parsed(
        work_dir=tmp_path,
        override=[],
        config_file=ini_file,
        root_dir=tmp_path,
        ansible=True,
    )

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(buffer=output, encoding="utf-8", line_buffering=True)
    state = State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )

    env_list = add_ansible_matrix(state)
    assert any("molecule" in name for name in env_list.envs)
    molecule_envs = [name for name in env_list.envs if name.startswith("molecule-")]
    assert len(molecule_envs) > 1
    assert "molecule-py3.12-2.19" in molecule_envs
    assert "molecule-py3.14-2.20" in molecule_envs


def test_add_ansible_matrix_molecule_auto_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test molecule envs excluded when no scenarios discovered.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    ini_file = tmp_path / "tox-ansible.ini"
    ini_file.write_text("[ansible]\n")
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    monkeypatch.chdir(tmp_path)
    source = discover_source(ini_file, None)
    parsed = Parsed(
        work_dir=tmp_path,
        override=[],
        config_file=ini_file,
        root_dir=tmp_path,
        ansible=True,
    )

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(buffer=output, encoding="utf-8", line_buffering=True)
    state = State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )

    env_list = add_ansible_matrix(state)
    assert not any("molecule" in name for name in env_list.envs)


def test_add_ansible_matrix_molecule_pyproject_true(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test molecule envs included via pyproject.toml molecule=true.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.tox-ansible]\nmolecule = "true"\n',
    )
    monkeypatch.chdir(tmp_path)
    source = discover_source(ini_file, None)
    parsed = Parsed(
        work_dir=tmp_path,
        override=[],
        config_file=ini_file,
        root_dir=tmp_path,
        ansible=True,
    )

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(buffer=output, encoding="utf-8", line_buffering=True)
    state = State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )

    env_list = add_ansible_matrix(state)
    assert any("molecule" in name for name in env_list.envs)


def test_add_ansible_matrix_molecule_pyproject_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test molecule envs excluded via pyproject.toml molecule=false.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    scenario_dir = tmp_path / "extensions" / "molecule" / "default"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "molecule.yml").touch()
    (tmp_path / "pyproject.toml").write_text(
        '[tool.tox-ansible]\nmolecule = "false"\n',
    )
    monkeypatch.chdir(tmp_path)
    source = discover_source(ini_file, None)
    parsed = Parsed(
        work_dir=tmp_path,
        override=[],
        config_file=ini_file,
        root_dir=tmp_path,
        ansible=True,
    )

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(buffer=output, encoding="utf-8", line_buffering=True)
    state = State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )

    env_list = add_ansible_matrix(state)
    assert not any("molecule" in name for name in env_list.envs)


def test_discover_integration_tests_targets(tmp_path: Path) -> None:
    """Test integration discovery via ansible-test targets.

    Args:
        tmp_path: Pytest fixture.
    """
    target = tmp_path / "tests" / "integration" / "targets" / "ping"
    target.mkdir(parents=True)
    (target / "tasks").mkdir()
    assert discover_integration_tests(tmp_path) is True


def test_discover_integration_tests_pytest(tmp_path: Path) -> None:
    """Test integration discovery via pytest modules.

    Args:
        tmp_path: Pytest fixture.
    """
    integration = tmp_path / "tests" / "integration"
    integration.mkdir(parents=True)
    (integration / "test_smoke.py").write_text("def test_smoke():\n    assert True\n")
    assert discover_integration_tests(tmp_path) is True


def test_discover_integration_tests_missing(tmp_path: Path) -> None:
    """Test integration discovery when no content exists.

    Args:
        tmp_path: Pytest fixture.
    """
    assert discover_integration_tests(tmp_path) is False


def test_add_ansible_matrix_strips_integration_without_tests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test integration envs are omitted when no integration content exists.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    ini_file = tmp_path / "tox-ansible.ini"
    ini_file.write_text("[ansible]\n")
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    monkeypatch.chdir(tmp_path)
    source = discover_source(ini_file, None)
    parsed = Parsed(
        work_dir=tmp_path,
        override=[],
        config_file=ini_file,
        root_dir=tmp_path,
        ansible=True,
    )

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(buffer=output, encoding="utf-8", line_buffering=True)
    state = State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )

    env_list = add_ansible_matrix(state)
    assert not any(name.startswith("integration-") for name in env_list.envs)
    assert any(name.startswith("unit-") for name in env_list.envs)
