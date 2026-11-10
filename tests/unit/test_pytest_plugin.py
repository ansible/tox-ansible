"""Unit tests for the tox-ansible pytest plugin."""

from __future__ import annotations

import sys

from pathlib import Path
from textwrap import dedent

import pytest


def test_inject_collection_paths_from_env_installs_finder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Collection paths from the environment initialize the Ansible loader."""
    try:
        from ansible.utils.collection_loader._collection_finder import (
            _AnsibleCollectionFinder,
        )
    except ImportError:
        pytest.skip("ansible-core not installed")

    collection_dir = tmp_path / "ansible_collections" / "ns" / "name"
    module_dir = collection_dir / "plugins" / "modules"
    module_dir.mkdir(parents=True)
    module_dir.joinpath("ping.py").write_text(
        dedent(
            """\
            DOCUMENTATION = {"module": "ping"}
            """,
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ANSIBLE_COLLECTIONS_PATH", str(tmp_path))

    from tox_ansible.pytest_plugin import inject_collection_paths_from_env

    inject_collection_paths_from_env()

    assert str(tmp_path) in sys.path
    assert any(isinstance(item, _AnsibleCollectionFinder) for item in sys.meta_path)


def test_inject_collection_paths_from_env_no_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty collection path env vars are a no-op."""
    monkeypatch.delenv("ANSIBLE_COLLECTIONS_PATH", raising=False)
    monkeypatch.delenv("ANSIBLE_COLLECTIONS_PATHS", raising=False)

    from tox_ansible.pytest_plugin import inject_collection_paths_from_env

    inject_collection_paths_from_env()


def test_pytest_configure_calls_inject(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pytest startup wires collection path injection."""
    calls: list[str] = []

    def fake_inject() -> None:
        calls.append("inject")

    monkeypatch.setattr(
        "tox_ansible.pytest_plugin.inject_collection_paths_from_env",
        fake_inject,
    )

    from tox_ansible.pytest_plugin import pytest_configure

    pytest_configure(config=pytest.Config.fromdictargs({}, []))
    assert calls == ["inject"]
