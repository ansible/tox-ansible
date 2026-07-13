"""Integration tests for downstream matrix configuration."""

from __future__ import annotations

import os
import subprocess

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pathlib import Path


def test_pyproject_downstream(
    module_fixture_dir: Path,
    tox_bin: Path,
) -> None:
    """Validate that downstream=true adds AAP extras and keeps upstream cores.

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
    assert any("2.16" in name for name in env_names)
    assert any("2.18" in name for name in env_names)
    assert any("2.19" in name for name in env_names)
    assert any("devel" in name for name in env_names)
    assert any("unit" in name for name in env_names)
