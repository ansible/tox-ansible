"""Basic tests."""
import json
import subprocess

from pathlib import Path

import pytest


def test_ansible_environments(module_fixture_dir: Path) -> None:
    """Test that the ansible environments are available.

    :param module_fixture_dir: pytest fixture to get the fixtures directory
    """
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
    module_fixture_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the ansible github matrix generation.

    Remove the GITHUB environment variable to test the default output.

    :param module_fixture_dir: pytest fixture to get the fixtures directory
    :param monkeypatch: pytest fixture to patch modules
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
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
