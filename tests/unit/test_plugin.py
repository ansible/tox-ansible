"""Unit plugin tests."""

from pathlib import Path

import pytest

from tox.config.cli.parser import Parsed
from tox.config.main import Config
from tox.config.source import discover_source

from tox_ansible.plugin import conf_commands_pre


def test_commands_pre(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test pre-command generation.

    Args:
        monkeypatch: Pytest fixture.
        tmp_path: Pytest fixture.
    """
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
    ).get_env("py39")

    conf.add_config(
        keys=["env_tmp_dir", "envtmpdir"],
        of_type=Path,
        default=tmp_path,
        desc="",
    )

    result = conf_commands_pre(env_conf=conf, c_name="test", c_namespace="test")
    number_commands = 15
    assert len(result) == number_commands, result
