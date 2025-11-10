"""Global testing fixtures.

The root package import below happens before the pytest workers are forked, so it
picked up by the initial coverage process for a source match.

Without it, coverage reports the following false positive error:

CoverageWarning: No data was collected. (no-data-collected)

This works in conjunction with the coverage source_pkg set to the package such that
a `coverage run --debug trace` shows the source package and file match.

<...>
Imported source package '<package>' as '/**/src/<package>/__init__.py'
<...>
Tracing '/**/src/<package>/__init__.py'
"""

from __future__ import annotations

import configparser
import os
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import tox_ansible  # noqa: F401


if TYPE_CHECKING:
    from collections.abc import Sequence

    from _pytest.python import Metafunc

GH_MATRIX_LENGTH = 40


def run(
    args: Sequence[str | Path] | str | Path,
    *,
    cwd: Path,
    check: bool = False,
    shell: bool = True,
    env: subprocess._ENV | None = None,
) -> subprocess.CompletedProcess[str]:
    """Utility function to run a command.

    Args:
        args: The command to run
        cwd: The current working directory
        check: Whether to raise an exception if the command fails
        shell: Whether to run the command in a shell
        env: The environment to run the command in

    Returns:
        A CompletedProcess with the result of the command
    """
    return subprocess.run(
        args=args,
        capture_output=True,
        check=check,
        cwd=str(cwd),
        shell=shell,
        text=True,
        env=env,
    )


@pytest.fixture(scope="session")
def tox_bin() -> Path:
    """Provide the path to the tox binary.

    Returns:
        Path to the tox binary
    """
    return Path(sys.executable).parent / "tox"


@pytest.fixture(scope="session")
def matrix_length() -> int:
    """Provide the length of the gh matrix.

    Returns:
        Length of the matrix
    """
    return GH_MATRIX_LENGTH


@pytest.fixture(scope="module")
def module_fixture_dir(request: pytest.FixtureRequest) -> Path:
    """Provide a module specific fixture directory.

    Args:
        request: pytest fixture request

    Returns:
        Path to the module specific fixture directory
    """
    cwd = Path(__file__).parent
    fixture_dir = cwd / "fixtures"
    return fixture_dir / request.path.relative_to(cwd).parent / request.path.stem


@pytest.fixture(autouse=True)
def _tox_in_tox(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable tox-in-tox.

    Args:
        monkeypatch: pytest fixture to patch modules
    """
    monkeypatch.delenv("TOX_ENV_NAME", raising=False)
    monkeypatch.delenv("TOX_WORK_DIR", raising=False)
    monkeypatch.delenv("TOX_ENV_DIR", raising=False)


@dataclass
class BasicEnvironment:
    """An structure for an environment.

    Attributes:
        name: The name of the environment
        config: The configuration entry for the environment
    """

    name: str
    config: dict[str, str]


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """Parametrize the basic environments and there configurations.

    Args:
        metafunc: Metadata for the test
    """
    if "basic_environment" in metafunc.fixturenames:
        cwd = Path(__file__).parent
        basic_dir = cwd / "fixtures" / "integration" / "test_basic"
        try:
            cmd = (
                f"{sys.executable} -m tox config --ansible "
                f"--root {basic_dir} --conf tox-ansible.ini -qq"
            )
            env = os.environ
            env.pop("TOX_ENV_DIR", None)
            env.pop("TOX_ENV_NAME", None)
            env.pop("TOX_WORK_DIR", None)
            env["NO_COLOR"] = "1"

            proc = run(
                args=cmd,
                check=True,
                cwd=basic_dir,
                env=env,
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout)
            print(exc.stderr)
            pytest.fail(exc.stderr)

        configs = configparser.ConfigParser()
        configs.read_string(proc.stdout)

        assert configs.sections()

        environment_configs = [
            BasicEnvironment(name=name, config=dict(configs[name])) for name in configs.sections()
        ]

        metafunc.parametrize(
            "basic_environment",
            environment_configs,
            ids=[x.replace(":", "-") for x in configs.sections()],
        )
