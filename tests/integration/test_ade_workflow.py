"""Tests for the ade-based collection install workflow."""

from __future__ import annotations

import shutil
import subprocess
import sys

from configparser import ConfigParser
from pathlib import Path

import pytest

from tests.conftest import run


def test_ade_workflow_config(
    module_fixture_dir: Path,
    tox_bin: Path,
) -> None:
    """Validate generated tox config uses ade for collection installation.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tox_bin: pytest fixture for tox binary
    """
    try:
        proc = run(
            f"{tox_bin} config --ansible --root {module_fixture_dir} --conf tox-ansible.ini -qq",
            cwd=module_fixture_dir,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        pytest.fail(exc.stderr)

    cfg_parser = ConfigParser()
    cfg_parser.read_string(proc.stdout)

    for env_name in cfg_parser.sections():
        if env_name == "testenv:galaxy":
            continue

        config = dict(cfg_parser[env_name])
        assert "ade install -e" in config["commands_pre"], (
            f"{env_name}: commands_pre should contain 'ade install -e'"
        )
        assert "ansible-dev-environment>=26.2.0" in config["deps"], (
            f"{env_name}: deps should contain 'ansible-dev-environment>=26.2.0'"
        )
        assert "ade" in config["allowlist_externals"], (
            f"{env_name}: allowlist_externals should contain 'ade'"
        )
        assert "ANSIBLE_COLLECTIONS_PATH=." in config["set_env"], (
            f"{env_name}: set_env should contain 'ANSIBLE_COLLECTIONS_PATH=.'"
        )


@pytest.mark.slow
def test_ade_workflow_e2e(
    module_fixture_dir: Path,
    tmp_path: Path,
) -> None:
    """Run a full tox --ansible workflow in an isolated venv.

    Copies the fixture collection to a temp directory, creates a fresh venv,
    installs tox + tox-ansible + ade, and runs a unit test environment end-to-end.
    This mimics exactly what a real user would do.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: pytest fixture for temporary directory
    """
    repo_root = Path(__file__).resolve().parents[2]

    collection_dir = tmp_path / "collection"
    shutil.copytree(module_fixture_dir, collection_dir)

    venv_dir = tmp_path / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )

    pip = str(venv_dir / "bin" / "pip")
    tox_bin = str(venv_dir / "bin" / "tox")

    result = subprocess.run(
        [pip, "install", "tox", "-e", str(repo_root)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    env_name = f"unit-py{py_ver}-2.19"

    proc = subprocess.run(
        [tox_bin, "--ansible", "--conf", "tox-ansible.ini", "-e", env_name],
        check=False,
        cwd=str(collection_dir),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, f"tox run failed:\n{proc.stdout}\n{proc.stderr}"
