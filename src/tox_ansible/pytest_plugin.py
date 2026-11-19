"""Pytest integration for collection unit and integration tests."""

from __future__ import annotations

import logging
import os
import sys


logger = logging.getLogger(__name__)

_ANSIBLE_COLLECTION_FINDER_MODULES = (
    "ansible.utils.collection_loader._collection_finder",
    "ansible.module_utils._internal._collection_loader._collection_finder",
)


def _load_ansible_collection_finder() -> type[object] | None:
    """Return ``_AnsibleCollectionFinder`` from the active ansible-core layout.

    Returns:
        The finder class, or ``None`` when ansible-core does not expose it.
    """
    for module_name in _ANSIBLE_COLLECTION_FINDER_MODULES:
        try:
            module = __import__(
                module_name,
                fromlist=["_AnsibleCollectionFinder"],
            )
        except ImportError:
            continue
        finder_cls = getattr(module, "_AnsibleCollectionFinder", None)
        if finder_cls is not None:
            return finder_cls
    return None


def inject_collection_paths_from_env() -> None:
    """Initialize Ansible collection paths from the active test environment.

    Mirrors the former ``pytest-ansible`` ``--ansible-unit-inject-only`` behavior:
    honor ``ANSIBLE_COLLECTIONS_PATH`` (or legacy ``ANSIBLE_COLLECTIONS_PATHS``),
    update ``sys.path``, and install ``AnsibleCollectionFinder`` so fully qualified
    plugins resolve in the pytest process.
    """
    env_paths = os.environ.get("ANSIBLE_COLLECTIONS_PATH") or os.environ.get(
        "ANSIBLE_COLLECTIONS_PATHS",
        "",
    )
    path_list = [path for path in env_paths.split(os.pathsep) if path]
    for path in path_list:
        sys.path.insert(0, path)
    if not path_list:
        return
    finder_cls = _load_ansible_collection_finder()
    if finder_cls is None:
        logger.debug("AnsibleCollectionFinder unavailable; skip collection inject")
        return
    acf = finder_cls(paths=path_list)
    acf._install()


def pytest_configure(config: object) -> None:
    """Initialize the Ansible collection loader before test collection.

    Args:
        config: Pytest configuration object.
    """
    _ = config
    inject_collection_paths_from_env()
