# cspell:ignore FQCNs
"""Impact report handling for tox-ansible.

This module provides functionality for loading and validating ImpactReport
JSON artifacts produced by content-plugin-finder.
"""

from __future__ import annotations

import json
import logging
import re
import sys

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from tox_ansible.plugin import Collection

logger = logging.getLogger(__name__)


@dataclass
class ImpactReport:
    """Impact report from content-plugin-finder.

    Attributes:
        collection: The collection name (namespace.name format).
        changed_files: List of changed file paths.
        affected_plugins: List of affected plugin fully-qualified names.
        molecule_scenarios: List of molecule scenario paths or names.
        integration_targets: List of integration target paths.
        reasons: Dict mapping targets to their impact reasons.
    """

    collection: str
    changed_files: list[str] = field(default_factory=list)
    affected_plugins: list[str] = field(default_factory=list)
    molecule_scenarios: list[str] = field(default_factory=list)
    integration_targets: list[str] = field(default_factory=list)
    reasons: dict[str, list[str]] = field(default_factory=dict)


def _validate_impact_path(path_str: str, project_dir: Path) -> None:
    """Validate an impact report path is safe (relative, no traversal).

    Args:
        path_str: The path string to validate.
        project_dir: The project root directory.

    Raises:
        ValueError: If the path is absolute or contains traversal.
    """
    path = Path(path_str)
    if path.is_absolute():
        msg = f"Absolute paths not allowed in impact report: {path_str}"
        raise ValueError(msg)
    # Resolve against project_dir and ensure it stays within
    resolved = (project_dir / path).resolve()
    try:
        resolved.relative_to(project_dir.resolve())
    except ValueError as exc:
        msg = f"Path traversal not allowed in impact report: {path_str}"
        raise ValueError(msg) from exc


# Pattern for safe target/scenario names: alphanumeric, underscore, hyphen, dot
SAFE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def _validate_safe_name(name: str, context: str) -> None:
    """Validate a name is safe for shell command use.

    Args:
        name: The name to validate.
        context: Context for error messages (e.g., "molecule scenario").

    Raises:
        ValueError: If the name contains unsafe characters.
    """
    if not SAFE_NAME_PATTERN.match(name):
        msg = (
            f"Unsafe {context} name '{name}': "
            "only alphanumeric, underscore, hyphen, and dot allowed"
        )
        raise ValueError(msg)


def _validate_impact_list_field(data: dict[str, Any], field_name: str) -> None:
    """Validate a list field in impact report data.

    Args:
        data: The parsed JSON data.
        field_name: The field name to validate.
    """
    if field_name not in data:
        return
    if not isinstance(data[field_name], list):
        err = f"Impact file '{field_name}' must be a list, got {type(data[field_name]).__name__}"
        logger.critical(err)
        sys.exit(1)
    for item in data[field_name]:
        if not isinstance(item, str):
            err = f"Impact file '{field_name}' items must be strings, got {type(item).__name__}"
            logger.critical(err)
            sys.exit(1)


def _validate_impact_reasons(data: dict[str, Any]) -> None:
    """Validate the reasons field in impact report data.

    Args:
        data: The parsed JSON data.
    """
    if "reasons" not in data:
        return
    if not isinstance(data["reasons"], dict):
        err = f"Impact file 'reasons' must be an object, got {type(data['reasons']).__name__}"
        logger.critical(err)
        sys.exit(1)
    for key, val in data["reasons"].items():
        if not isinstance(val, list):
            err = (
                f"Impact file 'reasons' values must be lists, got {type(val).__name__} for '{key}'"
            )
            logger.critical(err)
            sys.exit(1)


def _validate_impact_collection(
    data: dict[str, Any],
    collection: Collection | None,
) -> None:
    """Validate the collection field in impact report data.

    Args:
        data: The parsed JSON data.
        collection: Optional collection info for name validation.
    """
    if "collection" not in data:
        err = "Impact file missing required 'collection' field"
        logger.critical(err)
        sys.exit(1)

    if not isinstance(data["collection"], str):
        err = f"Impact file 'collection' must be a string, got {type(data['collection']).__name__}"
        logger.critical(err)
        sys.exit(1)

    if collection is not None:
        expected_collection = f"{collection.namespace}.{collection.name}"
        if data["collection"] != expected_collection:
            # Strip control characters to prevent log injection (CWE-117)
            safe_got = data["collection"].replace("\n", "\\n").replace("\r", "\\r")
            logger.critical(
                "Impact file collection mismatch: expected '%s', got '%s'",
                expected_collection,
                safe_got,
            )
            sys.exit(1)


def _resolve_impact_path(impact_file: str, project_dir: Path) -> Path:
    """Resolve an impact file path and verify it is a regular file.

    Args:
        impact_file: Path string (absolute or relative to project_dir).
        project_dir: The project root directory.

    Returns:
        The resolved absolute path.
    """
    impact_path = Path(impact_file)
    if not impact_path.is_absolute():
        impact_path = project_dir / impact_path

    if not impact_path.is_file():
        if impact_path.is_dir():
            err = f"Impact file path is a directory: {impact_path}"
        elif not impact_path.exists():
            err = f"Impact file not found: {impact_path}"
        else:
            err = f"Impact file is not a regular file: {impact_path}"
        logger.critical(err)
        sys.exit(1)

    return impact_path


def _read_impact_file(impact_path: Path) -> object:
    """Read and JSON-parse an impact file.

    Args:
        impact_path: Resolved path to the impact file.

    Returns:
        The parsed JSON data.
    """
    try:
        with impact_path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        err = f"Invalid JSON in impact file {impact_path}: {exc}"
        logger.critical(err)
        sys.exit(1)
    except UnicodeDecodeError as exc:
        err = f"Impact file is not valid UTF-8: {impact_path}: {exc}"
        logger.critical(err)
        sys.exit(1)
    except OSError as exc:
        err = f"Cannot read impact file {impact_path}: {exc}"
        logger.critical(err)
        sys.exit(1)


def load_impact_report(
    impact_file: str,
    project_dir: Path,
    collection: Collection | None = None,
) -> ImpactReport | None:
    """Load and validate an ImpactReport JSON file.

    Args:
        impact_file: Path to the ImpactReport JSON file.
        project_dir: The project root directory.
        collection: Optional collection info for name validation.

    Returns:
        The parsed ImpactReport, or None if impact_file is empty.
    """
    if not impact_file:
        return None

    impact_path = _resolve_impact_path(impact_file, project_dir)
    raw = _read_impact_file(impact_path)

    if not isinstance(raw, dict):
        err = f"Impact file must contain a JSON object, got {type(raw).__name__}"
        logger.critical(err)
        sys.exit(1)

    # Explicit typed binding after isinstance guard — removes type ambiguity for
    # static analysis tools that don't track sys.exit() as a terminator.
    json_data: dict[str, Any] = raw

    _validate_impact_collection(json_data, collection)

    list_fields = ("changed_files", "affected_plugins", "molecule_scenarios", "integration_targets")
    for field_name in list_fields:
        _validate_impact_list_field(json_data, field_name)

    _validate_impact_reasons(json_data)

    try:
        for path_str in json_data.get("changed_files", []):
            _validate_impact_path(path_str, project_dir)
        for path_str in json_data.get("molecule_scenarios", []):
            _validate_impact_path(path_str, project_dir)
            # Also validate the scenario name (last path component)
            scenario_name = Path(path_str).name
            _validate_safe_name(scenario_name, "molecule scenario")
        for path_str in json_data.get("integration_targets", []):
            _validate_impact_path(path_str, project_dir)
            # Enforce schema: integration_targets must be under tests/integration/targets/
            if not path_str.startswith("tests/integration/targets/"):
                logger.critical(
                    "Integration target '%s' must start with 'tests/integration/targets/'",
                    path_str,
                )
                sys.exit(1)
            # Also validate the target name (last path component)
            target_name = Path(path_str).name
            _validate_safe_name(target_name, "integration target")
    except ValueError as exc:
        logger.critical(str(exc))
        sys.exit(1)

    return ImpactReport(
        collection=json_data["collection"],
        changed_files=json_data.get("changed_files", []),
        affected_plugins=json_data.get("affected_plugins", []),
        molecule_scenarios=json_data.get("molecule_scenarios", []),
        integration_targets=json_data.get("integration_targets", []),
        reasons=json_data.get("reasons", {}),
    )
