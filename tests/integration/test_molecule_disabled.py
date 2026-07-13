"""Integration tests for molecule = false configuration."""

from __future__ import annotations

import os
import subprocess

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pathlib import Path


def test_molecule_disabled(
    module_fixture_dir: Path,
    tox_bin: Path,
) -> None:
    """Validate that molecule=false suppresses molecule envs even with scenarios present.

    The fixture has extensions/molecule/default/molecule.yml but pyproject.toml
    sets molecule = "false", so no molecule environments should appear.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tox_bin: pytest fixture for tox binary
    """
    try:
        proc = subprocess.run(
            [tox_bin, "list", "--ansible", "--root", str(module_fixture_dir)],
            capture_output=True,
            cwd=str(module_fixture_dir),
            text=True,
            check=True,
            shell=False,
            env=os.environ,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        pytest.fail(exc.stderr)

    env_names = proc.stdout.strip().splitlines()
    for name in env_names:
        assert "molecule" not in name, f"molecule should be disabled: {name}"
    assert any("unit" in name for name in env_names)
    assert any("sanity" in name for name in env_names)
    assert any("integration" in name for name in env_names)
