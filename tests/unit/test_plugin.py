"""Unit plugin tests."""

import json
import re

from pathlib import Path

import pytest

from tox.config.cli.parser import Parsed
from tox.config.main import Config
from tox.config.source import discover_source
from tox.config.types import EnvList

from tox_ansible.plugin import conf_commands_pre, generate_gh_matrix


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
    number_commands = 12
    assert len(result) == number_commands, result


def test_check_num_candidates_2(caplog: pytest.LogCaptureFixture) -> None:
    """Test the number of candidates check.

    Args:
        caplog: Pytest fixture.
    """
    environment_list = EnvList(envs=["integration-py3.9-py3.9"])
    with pytest.raises(SystemExit, match="1"):
        generate_gh_matrix(environment_list, "all")
    logs = caplog.text
    assert "Multiple python versions found" in logs


def test_check_num_candidates_0(caplog: pytest.LogCaptureFixture) -> None:
    """Test the number of candidates check.

    Args:
        caplog: Pytest fixture.
    """
    environment_list = EnvList(envs=["integration-foo-foo"])
    with pytest.raises(SystemExit, match="1"):
        generate_gh_matrix(environment_list, "all")
    logs = caplog.text
    assert "No python version found" in logs


@pytest.mark.parametrize("python", ("py313", "py3.13"))
def test_gen_version_matrix(python: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the version matrix generation.

    Args:
        python: Python version.
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    environment_list = EnvList(envs=[f"integration-{python}-2.15"])
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    gh_output = tmp_path / "matrix.json"
    monkeypatch.setenv("GITHUB_OUTPUT", str(gh_output))
    generate_gh_matrix(environment_list, "all")
    result = gh_output.read_text()
    json_string = re.match(r"envlist=(?P<json>.*)$", result)
    assert json_string
    json_result = json.loads(json_string.group("json"))
    assert json_result[0] == {
        "description": f"Integration tests using ansible-core 2.15 and python {python[2:]}",
        "factors": ["integration", python, "2.15"],
        "name": f"integration-{python}-2.15",
        "python": "3.13",
    }
