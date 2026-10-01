"""Integration tests for impact_file configuration support.

These tests require the tox-ansible plugin to be installed with the
impact_file feature. They will be skipped if --impact-file is not recognized.
"""

from __future__ import annotations

import os
import shutil
import subprocess

from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from pathlib import Path


def _impact_file_available(tox_bin: Path) -> bool:
    """Check if --impact-file flag is available in installed tox-ansible.

    Note: This checks the installed tox-ansible plugin, not the source version.
    The plugin is loaded via entry points, so PYTHONPATH doesn't help.
    """
    # Run without inheriting env to ensure we check the installed version
    env = {"PATH": os.environ.get("PATH", "")}
    proc = subprocess.run(
        [str(tox_bin), "--help"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return "--impact-file" in proc.stdout


@pytest.fixture(autouse=True)
def skip_if_impact_file_unavailable(tox_bin: Path) -> None:
    """Skip tests if impact_file feature is not available in installed plugin."""
    if not _impact_file_available(tox_bin):
        pytest.skip("--impact-file not available in installed tox-ansible")


def test_impact_file_empty_omits_both(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """When both molecule_scenarios and integration_targets are empty, omit both.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: Pytest temporary directory fixture
        tox_bin: pytest fixture for tox binary
    """
    project_dir = tmp_path / "project"
    shutil.copytree(module_fixture_dir, project_dir)

    try:
        proc = subprocess.run(
            [tox_bin, "--ansible", "-l", "--impact-file", "impact-empty.json"],
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
        pytest.fail(f"stdout:\n{exc.stdout}\n\nstderr:\n{exc.stderr}")

    env_names = proc.stdout.strip().splitlines()

    # No molecule or integration environments
    assert not any(name.startswith("molecule-") for name in env_names)
    assert not any(name.startswith("integration-") for name in env_names)
    # But unit, sanity, and galaxy are present
    assert any(name.startswith("unit-") for name in env_names)
    assert any(name.startswith("sanity-") for name in env_names)
    assert "galaxy" in env_names


def test_impact_file_molecule_only(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """When only molecule_scenarios is provided, omit integration environments.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: Pytest temporary directory fixture
        tox_bin: pytest fixture for tox binary
    """
    project_dir = tmp_path / "project"
    shutil.copytree(module_fixture_dir, project_dir)

    try:
        proc = subprocess.run(
            [tox_bin, "--ansible", "-l", "--impact-file", "impact-molecule-only.json"],
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
        pytest.fail(f"stdout:\n{exc.stdout}\n\nstderr:\n{exc.stderr}")

    env_names = proc.stdout.strip().splitlines()

    # Molecule environments are present
    assert any(name.startswith("molecule-") for name in env_names)
    # No integration environments
    assert not any(name.startswith("integration-") for name in env_names)


def test_impact_file_integration_only(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """When only integration_targets is provided, omit molecule environments.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: Pytest temporary directory fixture
        tox_bin: pytest fixture for tox binary
    """
    project_dir = tmp_path / "project"
    shutil.copytree(module_fixture_dir, project_dir)

    try:
        proc = subprocess.run(
            [tox_bin, "--ansible", "-l", "--impact-file", "impact-integration-only.json"],
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
        pytest.fail(f"stdout:\n{exc.stdout}\n\nstderr:\n{exc.stderr}")

    env_names = proc.stdout.strip().splitlines()

    # Integration environments are present
    assert any(name.startswith("integration-") for name in env_names)
    # No molecule environments
    assert not any(name.startswith("molecule-") for name in env_names)


def test_impact_file_both_present(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """When both molecule_scenarios and integration_targets are provided, include both.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: Pytest temporary directory fixture
        tox_bin: pytest fixture for tox binary
    """
    project_dir = tmp_path / "project"
    shutil.copytree(module_fixture_dir, project_dir)

    try:
        proc = subprocess.run(
            [tox_bin, "--ansible", "-l", "--impact-file", "impact-both.json"],
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
        pytest.fail(f"stdout:\n{exc.stdout}\n\nstderr:\n{exc.stderr}")

    env_names = proc.stdout.strip().splitlines()

    # Both molecule and integration environments are present
    assert any(name.startswith("molecule-") for name in env_names)
    assert any(name.startswith("integration-") for name in env_names)


def test_impact_file_no_file_preserves_behavior(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """Without --impact-file, normal discovery behavior is preserved.

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
        pytest.fail(f"stdout:\n{exc.stdout}\n\nstderr:\n{exc.stderr}")

    env_names = proc.stdout.strip().splitlines()

    # Both molecule and integration environments are present (normal discovery)
    assert any(name.startswith("molecule-") for name in env_names)
    assert any(name.startswith("integration-") for name in env_names)


def test_impact_file_invalid_json_exits(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """Invalid JSON in impact file causes tox to exit.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: Pytest temporary directory fixture
        tox_bin: pytest fixture for tox binary
    """
    project_dir = tmp_path / "project"
    shutil.copytree(module_fixture_dir, project_dir)

    # Create invalid JSON file
    invalid_file = project_dir / "invalid.json"
    invalid_file.write_text("{ not valid json }")

    proc = subprocess.run(
        [tox_bin, "--ansible", "-l", "--impact-file", "invalid.json"],
        capture_output=True,
        cwd=str(project_dir),
        text=True,
        check=False,
        shell=False,
        env=os.environ,
    )

    assert proc.returncode != 0
    assert "Invalid JSON" in proc.stderr or "Invalid JSON" in proc.stdout


def test_impact_file_collection_mismatch_exits(
    module_fixture_dir: Path,
    tmp_path: Path,
    tox_bin: Path,
) -> None:
    """Collection name mismatch causes tox to exit.

    Args:
        module_fixture_dir: pytest fixture for module fixture directory
        tmp_path: Pytest temporary directory fixture
        tox_bin: pytest fixture for tox binary
    """
    project_dir = tmp_path / "project"
    shutil.copytree(module_fixture_dir, project_dir)

    # Create impact file with wrong collection name
    wrong_collection = project_dir / "wrong-collection.json"
    wrong_collection.write_text('{"collection": "wrong.collection"}')

    proc = subprocess.run(
        [tox_bin, "--ansible", "config", "--impact-file", "wrong-collection.json"],
        capture_output=True,
        cwd=str(project_dir),
        text=True,
        check=False,
        shell=False,
        env=os.environ,
    )

    assert proc.returncode != 0
    assert "mismatch" in proc.stderr or "mismatch" in proc.stdout
