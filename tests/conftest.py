"""Global testing fixtures."""

from __future__ import annotations

import configparser
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
class BasicEnvironment:
    """An structure for an environment."""

    name: str
    config: dict[str, str]


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """Parametrize the basic environments and there configurations.

    :param metafunc: Metadata for the test
    """
    if "basic_environment" in metafunc.fixturenames:
        cwd = Path(__file__).parent
        basic_dir = cwd / "fixtures" / "integration" / "test_basic"
        try:
            cmd = (
                f"{sys.executable} -m tox config --ansible "
                f"--root {basic_dir} --conf tox-ansible.ini"
            )
            proc = subprocess.run(
                args=cmd,
                capture_output=True,
                cwd=str(basic_dir),
                text=True,
                check=True,
                shell=True,
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
            ids=configs.sections(),
        )
