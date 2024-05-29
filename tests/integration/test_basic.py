"""Basic tests."""

from __future__ import annotations

import json
import os
import subprocess

from typing import TYPE_CHECKING

import pytest

from tox_ansible.plugin import conf_passenv


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


def test_import() -> None:
    """Verify that module can be imported (used for coverage)."""
    x = conf_passenv()
    assert "GITHUB_TOKEN" in x
