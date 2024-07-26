"""Basic tests."""

from __future__ import annotations

import json
import os
import runpy
import subprocess

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pathlib import Path

    from ..conftest import BasicEnvironment  # noqa: TID252


def test_ansible_environments(module_fixture_dir: Path, tox_bin: Path) -> None:
    """Test that the ansible environments are available.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        tox_bin: pytest fixture to get the tox binary
    """
    try:
        proc = subprocess.run(
            f"{tox_bin} -l --ansible --conf {module_fixture_dir}/tox-ansible.ini",
            capture_output=True,
            cwd=str(module_fixture_dir),
            text=True,
            check=True,
            shell=True,
            env=os.environ,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        pytest.fail(exc.stderr)
    assert "integration" in proc.stdout
    assert "sanity" in proc.stdout
    assert "unit" in proc.stdout


def test_gh_matrix(
    module_fixture_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    tox_bin: Path,
) -> None:
    """Test that the ansible github matrix generation.

    Remove the GITHUB environment variable to test the default output.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        monkeypatch: pytest fixture to patch modules
        tox_bin: pytest fixture to get the tox binary
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)

    proc = subprocess.run(
        f"{tox_bin} --ansible --gh-matrix --root {module_fixture_dir} --conf tox-ansible.ini",
        capture_output=True,
        cwd=str(module_fixture_dir),
        text=True,
        check=True,
        shell=True,
        env=os.environ,
    )
    structured = json.loads(proc.stdout)
    assert isinstance(structured, list)
    assert structured
    for entry in structured:
        assert tuple(sorted(entry)) == ("description", "factors", "name", "python")
        assert isinstance(entry["description"], str)
        assert isinstance(entry["factors"], list)
        assert isinstance(entry["name"], str)
        assert isinstance(entry["python"], str)


def test_environment_config(
    basic_environment: BasicEnvironment,
) -> None:
    """Test that the ansible environment configurations are generated.

    Ensure the environment configurations are generated and look for information unlikely to change
    as a basic smoke test.

    Args:
        basic_environment: A dict representing the environment configuration
    """
    assert "py3" in basic_environment.name

    config = basic_environment.config

    assert config["allowlist_externals"]
    assert config["commands_pre"]
    assert config["commands"]
    assert config["pass_env"]

    assert "https://github.com/ansible/ansible/archive" in config["deps"]
    assert "XDG_CACHE_HOME" in config["set_env"]


def test_no_ansible_flag(module_fixture_dir: Path, tox_bin: Path) -> None:
    """Test exit plugin w/o ansible-flag.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        tox_bin: pytest fixture to get the tox binary

    """
    proc = subprocess.run(
        f"{tox_bin} --root {module_fixture_dir} --conf tox-ansible.ini",
        capture_output=True,
        cwd=str(module_fixture_dir),
        text=True,
        check=True,
        shell=True,
        env=os.environ,
    )
    assert "py: OK" in proc.stdout


def test_no_ansible_flag_gh(module_fixture_dir: Path, tox_bin: Path) -> None:
    """Test that the ansible flag is required for gh_matrix.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        tox_bin: pytest fixture to get the tox binary

    """
    with pytest.raises(subprocess.CalledProcessError) as exc:
        subprocess.run(
            f"{tox_bin} --gh-matrix --root {module_fixture_dir} --conf tox-ansible.ini",
            capture_output=True,
            cwd=str(module_fixture_dir),
            text=True,
            check=True,
            shell=True,
            env=os.environ,
        )
    assert "The --gh-matrix option requires --ansible" in exc.value.stdout


def test_tox_ini_msg(
    module_fixture_dir: Path,
    tox_bin: Path,
) -> None:
    """Test that a recommendation is provided to not use a tox.ini.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        tox_bin: pytest fixture to get the tox binary

    """
    with pytest.raises(subprocess.CalledProcessError) as exc:
        subprocess.run(
            f"{tox_bin} --ansible --root {module_fixture_dir} -e non-existent",
            capture_output=True,
            cwd=str(module_fixture_dir),
            text=True,
            check=True,
            shell=True,
            env=os.environ,
        )
    expected = "Using a default tox.ini file with tox-ansible plugin is not recommended"
    assert expected in exc.value.stdout


def test_tox_invalid(
    module_fixture_dir: Path,
    tox_bin: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test an invalid environment is ignored. The plugin should not raise an error.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        tox_bin: pytest fixture to get the tox binary
        monkeypatch: pytest fixture to patch modules
        capsys: pytest fixture to capture stdout/stderr
    """
    monkeypatch.setattr("tox_ansible.plugin.ENV_LIST", "insanity-py3.13-devel")

    monkeypatch.setattr(
        "sys.argv",
        [
            str(tox_bin),
            "config",
            "--ansible",
            "--root",
            str(module_fixture_dir),
            "--conf",
            "tox-ansible.ini",
        ],
    )
    with pytest.raises(SystemExit, match="0"):
        runpy.run_module("tox", run_name="__main__")
    captured = capsys.readouterr()
    assert "Unable to find galaxy.yml file" not in captured.out


def test_setting_matrix_scope(
    module_fixture_dir: Path,
    tox_bin: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test setting the matrix scope to a specific section.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        tox_bin: pytest fixture to get the tox binary
        monkeypatch: pytest fixture to patch modules
        capsys: pytest fixture to capture stdout/stderr
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.chdir(module_fixture_dir)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(tox_bin),
            "--ansible",
            "--gh-matrix",
            "--matrix-scope",
            "integration",
            "--conf",
            "tox-ansible.ini",
        ],
    )
    with pytest.raises(SystemExit, match="0"):
        runpy.run_module("tox", run_name="__main__")
    captured = capsys.readouterr()
    structured = json.loads(captured.out)
    assert isinstance(structured, list)
    assert all(entry["name"].startswith("integration") for entry in structured)


def test_action_not_output(
    module_fixture_dir: Path,
    tox_bin: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test for exit when action is set but not output.

    Args:
        module_fixture_dir: pytest fixture to get the fixtures directory
        tox_bin: pytest fixture to get the tox binary
        monkeypatch: pytest fixture to patch modules
        capsys: pytest fixture to capture
    """
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.chdir(module_fixture_dir)
    monkeypatch.setattr(
        "sys.argv",
        [
            str(tox_bin),
            "--ansible",
            "--gh-matrix",
            "--conf",
            "tox-ansible.ini",
        ],
    )

    with pytest.raises(SystemExit, match="1"):
        runpy.run_module("tox", run_name="__main__")
    captured = capsys.readouterr()
    assert "GITHUB_OUTPUT environment variable not set" in captured.out
