"""User provided configuration."""

import subprocess

from configparser import ConfigParser
from pathlib import Path

import pytest


def test_user_provided(
    module_fixture_dir: Path,
) -> None:
    """Test supplemental user configuration.

    :param module_fixture_dir: pytest fixture for module fixture directory
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
    assert "specific" in cfg_parser.get("testenv:integration-py3.11-devel", "pass_env")
