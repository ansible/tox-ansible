"""Test the use of a generic type with tox.

These are specific to PR https://github.com/tox-dev/tox/pull/3288

When merged the 2nd test can be switched to a SystemExit like test #1
The types override for List/list and the related ruff noqa's in plugin.py can be removed.
"""

import json
import runpy

from pathlib import Path

import pytest


def test_type_current(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    module_fixture_dir: Path,
    matrix_length: int,
) -> None:
    """Test the current runtime for a gh matrix.

    Args:
        capsys: pytest fixture to capture stdout and stderr
        monkeypatch: pytest fixture to patch modules
        module_fixture_dir: pytest fixture to provide a module specific fixture directory
        matrix_length: pytest fixture to provide the length of the gh matrix
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.chdir(module_fixture_dir)
    args = [
        "--ansible",
        "--gh-matrix",
        "--conf",
        "tox-ansible.ini",
    ]
    out = runpy.run_module("tox")
    with pytest.raises(SystemExit):
        out["run"](args=args)
    captured = capsys.readouterr()
    matrix = json.loads(captured.out)
    matrix_len = matrix_length
    assert len(matrix) == matrix_len
    for entry in matrix:
        assert entry["description"]
        assert entry["factors"]
