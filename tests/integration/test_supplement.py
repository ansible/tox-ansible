"""User provided configuration."""
from pathlib import Path

import pytest

from tox.config.loader.memory import MemoryLoader
from tox.provision import provision
from tox.run import setup_state


def test_user_provided(
    monkeypatch: pytest.MonkeyPatch,
    module_fixture_dir: Path,
) -> None:
    """Test supplemental user configuration.

    :param monkeypatch: pytest fixture for patching
    :param module_fixture_dir: pytest fixture for module fixture directory
    """
    monkeypatch.chdir(module_fixture_dir)

    target_env = "integration-py3.11-devel"
    args = [
        "-e",
        target_env,
        "--ansible",
        "--no-provision",
        "--root",
        str(module_fixture_dir),
    ]
    state = setup_state(args)

    provision(state)

    # Populate the list
    _envs = list(state.envs.iter())

    # pylint: disable=protected-access
    assert state.envs._defined_envs_  # noqa: SLF001
    env_config = state.envs._defined_envs_[target_env]  # noqa: SLF001
    loader = env_config.env.conf.loaders[0]
    assert isinstance(loader, MemoryLoader)
    # pylint: enable=protected-access

    config = loader.raw

    assert "root" in config["allowlist_externals"]
    assert "root" in config["deps"]
    assert "root" in config["commands"]
    assert "root" in config["commands_pre"]
    assert "root" in config["setenv"]

    assert "specific" in config["passenv"]
