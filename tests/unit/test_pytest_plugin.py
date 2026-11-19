"""Unit tests for the tox-ansible pytest plugin."""

from __future__ import annotations

import builtins
import sys
import types

from collections.abc import Mapping, Sequence
from pathlib import Path
from textwrap import dedent

import pytest

from tox_ansible.pytest_plugin import (
    _ANSIBLE_COLLECTION_FINDER_MODULES,
    _load_ansible_collection_finder,
    inject_collection_paths_from_env,
    pytest_configure,
)


pytest.importorskip("ansible")


def test_inject_collection_paths_from_env_installs_finder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Collection paths from the environment initialize the Ansible loader.

    Args:
        tmp_path: Pytest fixture for a temporary directory.
        monkeypatch: Pytest fixture to patch modules and environment.
    """
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

    inject_collection_paths_from_env()

    finder_cls = _load_ansible_collection_finder()
    assert finder_cls is not None
    assert str(tmp_path) in sys.path
    assert any(isinstance(item, finder_cls) for item in sys.meta_path)


def test_load_ansible_collection_finder_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ansible-core exposes no finder, loading returns ``None``.

    Args:
        monkeypatch: Pytest fixture to patch modules and environment.
    """
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name in _ANSIBLE_COLLECTION_FINDER_MODULES:
            msg = "forced for test"
            raise ImportError(msg)
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert _load_ansible_collection_finder() is None


def test_load_ansible_collection_finder_falls_back_to_internal_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy import paths without a finder class fall through to newer layouts.

    Args:
        monkeypatch: Pytest fixture to patch modules and environment.
    """
    real_import = builtins.__import__
    legacy_module = _ANSIBLE_COLLECTION_FINDER_MODULES[0]
    internal_module = _ANSIBLE_COLLECTION_FINDER_MODULES[1]

    class FakeFinder:
        pass

    def fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name == legacy_module:
            return types.ModuleType(name)
        if name == internal_module:
            module = types.ModuleType(name)
            module._AnsibleCollectionFinder = FakeFinder
            return module
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert _load_ansible_collection_finder() is FakeFinder


def test_inject_collection_paths_from_env_no_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty collection path env vars are a no-op.

    Args:
        monkeypatch: Pytest fixture to patch modules and environment.
    """
    monkeypatch.delenv("ANSIBLE_COLLECTIONS_PATH", raising=False)
    monkeypatch.delenv("ANSIBLE_COLLECTIONS_PATHS", raising=False)

    inject_collection_paths_from_env()


def test_inject_collection_paths_skips_without_finder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing ansible-core collection finder support is ignored.

    Args:
        monkeypatch: Pytest fixture to patch modules and environment.
    """
    monkeypatch.setenv("ANSIBLE_COLLECTIONS_PATH", "/collections")
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> object:
        if name in _ANSIBLE_COLLECTION_FINDER_MODULES:
            msg = "forced for test"
            raise ImportError(msg)
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    inject_collection_paths_from_env()


def test_pytest_configure_calls_inject(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pytest startup wires collection path injection.

    Args:
        monkeypatch: Pytest fixture to patch modules and environment.
    """
    calls: list[str] = []

    def fake_inject() -> None:
        calls.append("inject")

    monkeypatch.setattr(
        "tox_ansible.pytest_plugin.inject_collection_paths_from_env",
        fake_inject,
    )

    pytest_configure(config=object())
    assert calls == ["inject"]
