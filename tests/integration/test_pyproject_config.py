"""Integration tests for pyproject.toml configuration support."""

from __future__ import annotations

import os
import shutil
import subprocess

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pathlib import Path


def test_pyproject_skip(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """Validate that [tool.tox-ansible] skip filters environments.

    The fixture pyproject.toml skips "devel" and "milestone", so no
    environment names should contain those strings.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: Pytest temporary directory fixture
        tox_bin: pytest fixture for tox binary
    """
    project_dir = tmp_path / "project"
    shutil.copytree(module_fixture_dir, project_dir)

    try:
        proc = subprocess.run(
            [tox_bin, "--ansible", "-l"],
            capture_output=True,
            cwd=str(project_dir),
            text=True,
            check=True,
            shell=False,
            env=os.environ,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        pytest.fail(exc.stderr)

    warning = "Using a default tox.ini file with tox-ansible plugin is not recommended"
    assert warning not in proc.stdout
    assert warning not in proc.stderr

    env_names = proc.stdout.strip().splitlines()
    for name in env_names:
        assert "devel" not in name, f"devel should be skipped: {name}"
        assert "milestone" not in name, f"milestone should be skipped: {name}"
    assert any("unit" in name for name in env_names)
    assert any("sanity" in name for name in env_names)
    assert any("integration" in name for name in env_names)
