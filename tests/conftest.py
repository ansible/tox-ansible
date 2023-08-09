"""Global testing fixtures."""

from __future__ import annotations

import configparser
import os
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from _pytest.python import Metafunc


@pytest.fixture(scope="module")
def module_fixture_dir(request: pytest.FixtureRequest) -> Path:
    """Provide a module specific fixture directory.

    :param request: pytest fixture request
    :return: path to the module specific fixture directory
    """
    cwd = Path(__file__).parent
    fixture_dir = cwd / "fixtures"
    test_dir = fixture_dir / request.path.relative_to(cwd).parent / request.path.stem
    return test_dir


@pytest.fixture(autouse=True)
def _tox_in_tox(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable tox-in-tox.

    :param monkeypatch: pytest fixture to patch modules
    """
    monkeypatch.delenv("TOX_ENV_NAME", raising=False)
    monkeypatch.delenv("TOX_WORK_DIR", raising=False)
    monkeypatch.delenv("TOX_ENV_DIR", raising=False)


@dataclass
class ToxEnvironment:
    """An structure for an environment."""

    name: str
    config: dict[str, str]


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """Parametrize the basic environments and there configurations.

    :param metafunc: Metadata for the test
    """
    if "basic_environment" in metafunc.fixturenames:
        environment_configs = generate_environments("test_basic")
        metafunc.parametrize(
            "basic_environment",
            environment_configs,
            ids=[env.name for env in environment_configs],
        )
    if "skip_environment" in metafunc.fixturenames:
        environment_configs = generate_environments("test_skip")
        metafunc.parametrize(
            "skip_environment",
            environment_configs,
            ids=[env.name for env in environment_configs],
        )


def generate_environments(directory: str) -> list[ToxEnvironment]:
    """Generate the list of environments.

    :param directory: The fixture directory to use
    :returns: The environments and the ids
    """
    cwd = Path(__file__).parent
    basic_dir = cwd / "fixtures" / "integration" / directory
    try:
        cmd = (
            f"{sys.executable} -m tox config --ansible "
            f"--root {basic_dir} --conf tox-ansible.ini"
        )
        env = os.environ
        env.pop("TOX_ENV_DIR", None)
        env.pop("TOX_ENV_NAME", None)
        env.pop("TOX_WORK_DIR", None)

        proc = subprocess.run(
            args=cmd,
            capture_output=True,
            check=True,
            cwd=str(basic_dir),
            env=env,
            shell=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        pytest.fail(exc.stderr)

    configs = configparser.ConfigParser()
    configs.read_string(proc.stdout)

    assert configs.sections()

    environment_configs = [
        ToxEnvironment(name=name, config=dict(configs[name])) for name in configs.sections()
    ]

    return environment_configs
