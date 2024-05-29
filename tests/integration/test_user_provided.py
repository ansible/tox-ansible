"""User provided configuration."""

import json
import subprocess

from configparser import ConfigParser
from pathlib import Path

import pytest


def test_user_provided(
    module_fixture_dir: Path,
) -> None:
    """Test supplemental user configuration.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
    """
    try:
        proc = subprocess.run(
            f"tox config --ansible --root {module_fixture_dir} --conf tox-ansible.ini",
            capture_output=True,
            cwd=str(module_fixture_dir),
            text=True,
            check=True,
            shell=True,
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
    module_fixture_dir: Path,
    matrix_length: int,
) -> None:
    """Test supplemental user configuration for matrix generation.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        matrix_length: pytest fixture for matrix length
    """
    proc = subprocess.run(
        f"tox --ansible --root {module_fixture_dir} --gh-matrix --conf tox-ansible.ini",
        capture_output=True,
        cwd=str(module_fixture_dir),
        text=True,
        check=True,
        shell=True,
    )
    matrix = json.loads(proc.stdout)
    matrix_len = matrix_length
    assert len(matrix) == matrix_len
    for entry in matrix:
        assert entry["description"]
        assert entry["factors"]
