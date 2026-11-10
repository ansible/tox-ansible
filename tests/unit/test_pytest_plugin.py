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
