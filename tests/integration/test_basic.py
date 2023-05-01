"""Basic tests."""
import json
import subprocess

from pathlib import Path
from typing import Annotated

import os
import pytest


def test_ansible_environments(module_fixture_dir: Annotated[Path, pytest.fixture]) -> None:
    """Test that the ansible environments are available.

    :param module_fixture_dir: pytest fixture to get the fixtures directory
    """
    for envvar in os.environ:
        if envvar.startswith("TOX_"):
            print(f"{envvar}={os.environ[envvar]}")
    try:
        proc = subprocess.run(
            f"tox -l --ansible  --root {module_fixture_dir}",
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
    assert "integration" in proc.stdout
    assert "sanity" in proc.stdout
    assert "unit" in proc.stdout


def test_gh_matrix(
    module_fixture_dir: Annotated[Path, pytest.fixture],
) -> None:
    """Test that the ansible github matrix generation.

    :param module_fixture_dir: pytest fixture to get the fixtures directory
    """
    proc = subprocess.run(
        f"tox --ansible --gh-matrix --root {module_fixture_dir}",
        capture_output=True,
        cwd=str(module_fixture_dir),
        text=True,
        check=True,
        shell=True,
    )
    structured = json.loads(proc.stdout)
    assert isinstance(structured, list)
    assert structured
    for entry in structured:
        assert tuple(sorted(entry)) == ("factors", "name", "python")
        assert isinstance(entry["factors"], list)
        assert isinstance(entry["name"], str)
        assert isinstance(entry["python"], str)
