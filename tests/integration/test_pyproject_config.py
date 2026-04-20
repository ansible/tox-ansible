"""Integration tests for pyproject.toml configuration support."""

from __future__ import annotations

import os
import subprocess

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pathlib import Path


def test_pyproject_skip(
    module_fixture_dir: Path,
    tox_bin: Path,
) -> None:
    """Validate that [tool.tox-ansible] skip filters environments.

    The fixture pyproject.toml skips "devel" and "milestone", so no
    environment names should contain those strings.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tox_bin: pytest fixture for tox binary
    """
    try:
        proc = subprocess.run(
            f"{tox_bin} list --ansible --root {module_fixture_dir}",
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

    env_names = proc.stdout.strip().splitlines()
    for name in env_names:
        assert "devel" not in name, f"devel should be skipped: {name}"
        assert "milestone" not in name, f"milestone should be skipped: {name}"
    assert any("unit" in name for name in env_names)
    assert any("sanity" in name for name in env_names)
    assert any("integration" in name for name in env_names)
