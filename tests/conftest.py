"""Global testing fixtures."""

from pathlib import Path

import pytest


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
def tox_in_tox(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable tox-in-tox.

    :param monkeypatch: pytest fixture to patch modules
    """
    monkeypatch.delenv("TOX_ENV_NAME", raising=False)
    monkeypatch.delenv("TOX_WORK_DIR", raising=False)
    monkeypatch.delenv("TOX_ENV_DIR", raising=False)
