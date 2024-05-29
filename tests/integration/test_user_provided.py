"""User provided configuration."""

import json
import os
import subprocess

from configparser import ConfigParser
from pathlib import Path

import pytest


def test_user_provided(
    module_fixture_dir: Path,
    tox_bin: Path,
) -> None:
    """Test supplemental user configuration.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tox_bin: pytest fixture for tox binary
    """
    try:
        proc = subprocess.run(
            f"{tox_bin} config --ansible --root {module_fixture_dir} --conf tox-ansible.ini",
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
    cfg_parser = ConfigParser()
    cfg_parser.read_string(proc.stdout)
    for env_name in cfg_parser.sections():
        assert cfg_parser.get(env_name, "allowlist_externals") == "root"
        assert cfg_parser.get(env_name, "commands_pre") == "root"
        assert cfg_parser.get(env_name, "commands") == "root"
        assert cfg_parser.get(env_name, "deps") == "root"
        assert "root" in cfg_parser.get(env_name, "set_env")
        assert "milestone" not in env_name
    assert "specific" in cfg_parser.get("testenv:integration-py3.11-devel", "pass_env")


def test_user_provided_matrix_success(
    matrix_length: int,
    module_fixture_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    tox_bin: Path,
) -> None:
    """Test supplemental user configuration for matrix generation.

    Args:
        matrix_length: pytest fixture for matrix length
        module_fixture_dir: pytest fixture for module fixture directory
        monkeypatch: pytest fixture to patch modules
        tox_bin: pytest fixture for tox binary
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    proc = subprocess.run(
        f"{tox_bin} --ansible --root {module_fixture_dir} --gh-matrix --conf tox-ansible.ini",
        capture_output=True,
        cwd=str(module_fixture_dir),
        text=True,
        check=True,
        shell=True,
        env=os.environ,
    )
    matrix = json.loads(proc.stdout)
    matrix_len = matrix_length
    assert len(matrix) == matrix_len
    for entry in matrix:
        assert entry["description"]
        assert entry["factors"]
