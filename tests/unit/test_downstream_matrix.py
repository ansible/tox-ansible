"""Unit tests for the downstream matrix flag (ADR-001)."""

from __future__ import annotations

import io

from typing import TYPE_CHECKING

from tox.config.cli.parse import Options
from tox.config.cli.parser import Parsed
from tox.config.source import discover_source
from tox.report import ToxHandler
from tox.session.state import State

from tox_ansible.plugin import _load_ansible_config, add_ansible_matrix


if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _make_state(config_file: Path) -> State:
    """Create a tox state for configuration resolution tests.

    Args:
        config_file: The tox configuration file.

    Returns:
        The configured tox state.
    """
    source = discover_source(config_file, None)
    parsed = Parsed(
        work_dir=config_file.parent / ".tox",
        override=[],
        config_file=config_file,
        root_dir=config_file.parent,
        ansible=True,
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


def test_load_ansible_config_downstream_pyproject(tmp_path: Path) -> None:
    """Test loading downstream=true from pyproject.toml.

    Args:
        tmp_path: Pytest fixture.
    """
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(
        '[tool.tox]\nrequires = ["tox>=4.2"]\n[tool.tox-ansible]\ndownstream = true\n',
    )

    result = _load_ansible_config(_make_state(config_file))

    assert result.downstream is True
    assert not result.skip


def test_load_ansible_config_downstream_ini(tmp_path: Path) -> None:
    """Test loading downstream=true from tox-ansible.ini.

    Args:
        tmp_path: Pytest fixture.
    """
    config_file = tmp_path / "tox-ansible.ini"
    config_file.write_text("[ansible]\ndownstream = true\n")

    result = _load_ansible_config(_make_state(config_file))

    assert result.downstream is True


def test_load_ansible_config_downstream_string_false(tmp_path: Path) -> None:
    """Test quoted TOML 'false' does not enable downstream.

    Args:
        tmp_path: Pytest fixture.
    """
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(
        '[tool.tox]\nrequires = ["tox>=4.2"]\n[tool.tox-ansible]\ndownstream = "false"\n',
    )

    result = _load_ansible_config(_make_state(config_file))

    assert result.downstream is False


def test_add_ansible_matrix_default_excludes_extras(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default matrix does not include DOWNSTREAM_EXTRA cores.

    Args:
        tmp_path: Pytest fixture for temporary directory.
        monkeypatch: Pytest fixture for patching.
    """
    ini_file = tmp_path / "tox-ansible.ini"
    ini_file.write_text("[ansible]\n")
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    monkeypatch.chdir(tmp_path)

    env_list = add_ansible_matrix(_make_state(ini_file))
    assert not any("2.16" in name for name in env_list.envs)
    assert not any("2.18" in name for name in env_list.envs)
    assert any("2.19" in name for name in env_list.envs)


def test_add_ansible_matrix_downstream_extends(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test downstream=true unions AAP extras onto the upstream matrix.

    Args:
        tmp_path: Pytest fixture for temporary directory.
        monkeypatch: Pytest fixture for patching.
    """
    ini_file = tmp_path / "tox-ansible.ini"
    ini_file.write_text("[ansible]\ndownstream = true\n")
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    monkeypatch.chdir(tmp_path)

    env_list = add_ansible_matrix(_make_state(ini_file))
    assert any("2.16" in name for name in env_list.envs)
    assert any("2.18" in name for name in env_list.envs)
    assert any("2.19" in name for name in env_list.envs)
    assert any("devel" in name for name in env_list.envs)
    assert "unit-py3.12-2.16" in env_list.envs
    assert "unit-py3.13-2.18" in env_list.envs
    assert not any("py3.14-2.16" in name for name in env_list.envs)


def test_add_ansible_matrix_downstream_with_skip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test skip still filters the unioned downstream matrix.

    Args:
        tmp_path: Pytest fixture for temporary directory.
        monkeypatch: Pytest fixture for patching.
    """
    ini_file = tmp_path / "tox-ansible.ini"
    ini_file.write_text("[ansible]\ndownstream = true\nskip =\n    2.16\n    devel\n")
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test\nversion: 1.0.0")
    monkeypatch.chdir(tmp_path)

    env_list = add_ansible_matrix(_make_state(ini_file))
    for env_name in env_list.envs:
        assert "2.16" not in env_name
        assert "devel" not in env_name
    assert any("2.18" in name for name in env_list.envs)
