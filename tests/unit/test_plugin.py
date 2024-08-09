"""Unit plugin tests."""
from __future__ import annotations

import io
import json
import re

from pathlib import Path

import pytest
import yaml

from tox.config.cli.parse import Options
from tox.config.cli.parser import Parsed
from tox.config.loader.memory import MemoryLoader
from tox.config.main import Config
from tox.config.source import discover_source
from tox.config.types import EnvList
from tox.report import ToxHandler
from tox.session.state import State

from tox_ansible.plugin import (
    conf_commands,
    conf_commands_pre,
    conf_deps,
    generate_gh_matrix,
    get_collection_name,
    tox_add_env_config,
)


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


def test_gen_version_matrix_with_nl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the version matrix generation when it contains a newline.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    environment_list = EnvList(envs=["integration-py3.13-2.18"])
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    gh_output = tmp_path / "matrix.json"
    monkeypatch.setenv("GITHUB_OUTPUT", str(gh_output))

    json_dumps = json.dumps

    def json_dumps_mock(result: list[dict[str, str]]) -> str:
        """Mock json.dumps.

        Args:
            result: Result.

        Returns:
            str: JSON string.
        """
        return json_dumps(result, indent=4)

    monkeypatch.setattr("json.dumps", json_dumps_mock)

    generate_gh_matrix(environment_list, "all")
    result = gh_output.read_text()
    assert result.startswith("envlist<<EOF")


def test_get_collection_name_file_missing(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the collection name retrieval when the file is missing.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture for log capture
    """
    with pytest.raises(SystemExit, match="1"):
        get_collection_name(tmp_path / "galaxy.yml")
    logs = caplog.text
    assert "Unable to find galaxy.yml" in logs


def test_get_collection_name_broken(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the collection name retrieval when the file is missing.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture for log capture
    """
    galaxy_file = tmp_path / "galaxy.yml"
    contents = {"namespace": "test", "no_name": "test"}
    galaxy_file.write_text(yaml.dump(contents))
    with pytest.raises(SystemExit, match="1"):
        get_collection_name(tmp_path / "galaxy.yml")
    logs = caplog.text
    assert "Unable to find 'name' in galaxy.yml" in logs


def test_get_collection_name_success(
    tmp_path: Path,
) -> None:
    """Test the collection name retrieval when the file is missing.

    Args:
        tmp_path: Pytest fixture.
    """
    galaxy_file = tmp_path / "galaxy.yml"
    contents = {"namespace": "test", "name": "test"}
    galaxy_file.write_text(yaml.dump(contents))
    name, namespace = get_collection_name(tmp_path / "galaxy.yml")
    assert name == "test"
    assert namespace == "test"


def test_conf_commands_unit(tmp_path: Path) -> None:
    """Test the conf_commands function.

    Args:
        tmp_path: Pytest fixture.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
    ).get_env("unit-py3.13-2.18")

    result = conf_commands(
        env_conf=conf,
        c_name="test",
        c_namespace="test",
        test_type="unit",
        pos_args=None,
    )
    assert len(result) == 1
    assert result[0] == "python3 -m pytest --ansible-unit-inject-only ./tests/unit"


def test_conf_commands_sanity(tmp_path: Path) -> None:
    """Test the conf_commands function.

    Args:
        tmp_path: Pytest fixture.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
    ).get_env("sanity-py3.13-2.18")

    conf.add_config(
        keys=["env_tmp_dir", "envtmpdir"],
        of_type=Path,
        default=tmp_path,
        desc="",
    )

    result = conf_commands(
        env_conf=conf,
        c_name="test",
        c_namespace="test",
        test_type="sanity",
        pos_args=None,
    )
    assert len(result) == 1
    assert "ansible-test sanity" in result[0]


def test_conf_commands_integration(tmp_path: Path) -> None:
    """Test the conf_commands function.

    Args:
        tmp_path: Pytest fixture.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
    ).get_env("integration-py3.13-2.18")

    result = conf_commands(
        env_conf=conf,
        c_name="test",
        c_namespace="test",
        test_type="integration",
        pos_args=None,
    )
    assert len(result) == 1
    assert result[0] == "python3 -m pytest --ansible-unit-inject-only ./tests/integration"


def test_conf_commands_invalid(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test the conf_commands function.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture for log capture
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
    ).get_env("invalid-py3.13-2.18")

    with pytest.raises(SystemExit, match="1"):
        conf_commands(
            env_conf=conf,
            c_name="test",
            c_namespace="test",
            test_type="invalid",
            pos_args=None,
        )

    logs = caplog.text
    assert "Unknown test type" in logs


def test_conf_deps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the conf_commands function.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture for patching.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    source = discover_source(ini_file, None)

    (tmp_path / "test-requirements.txt").write_text("test-requirement")
    (tmp_path / "requirements.txt").write_text("requirement")
    (tmp_path / "requirements-test.txt").write_text("requirement-test")
    monkeypatch.setattr("tox_ansible.plugin.TOX_WORK_DIR", tmp_path)

    conf = Config.make(
        Parsed(work_dir=tmp_path, override=[], config_file=ini_file, root_dir=tmp_path),
        pos_args=[],
        source=source,
    ).get_env("unit-py3.13-2.18")

    result = conf_deps(env_conf=conf, test_type="unit")
    assert "test-requirement" in result
    assert "requirement" in result
    assert "requirement-test" in result


def test_tox_add_env_config_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the tox_add_env_config function.

    Args:
        tmp_path: Pytest fixture for temporary directory.
        monkeypatch: Pytest fixture for patching.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test")
    monkeypatch.chdir(tmp_path)
    source = discover_source(ini_file, None)
    parsed = Parsed(
        work_dir=tmp_path,
        override=[],
        config_file=ini_file,
        root_dir=tmp_path,
        ansible=True,
    )

    env_conf = Config.make(
        parsed=parsed,
        pos_args=[],
        source=source,
    ).get_env("unit-py3.13-2.18")

    env_conf.add_config(
        keys=["env_tmp_dir", "envtmpdir"],
        of_type=Path,
        default=tmp_path,
        desc="",
    )

    env_conf.add_config(
        keys=["env_dir", "envdir"],
        of_type=Path,
        default=tmp_path,
        desc="",
    )

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(
        buffer=output,
        encoding="utf-8",
        line_buffering=True,
    )

    state = State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )

    tox_add_env_config(env_conf, state)

    assert isinstance(env_conf.loaders[0], MemoryLoader)
    assert (
        env_conf.loaders[0].raw["description"]
        == "Unit tests using ansible-core 2.18 and python 3.13"
    )


def test_tox_add_env_config_invalid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the tox_add_env_config function.

    Args:
        tmp_path: Pytest fixture for temporary directory.
        monkeypatch: Pytest fixture for patching.
    """
    ini_file = tmp_path / "tox.ini"
    ini_file.touch()
    (tmp_path / "galaxy.yml").write_text("namespace: test\nname: test")
    monkeypatch.chdir(tmp_path)
    source = discover_source(ini_file, None)
    parsed = Parsed(
        work_dir=tmp_path,
        override=[],
        config_file=ini_file,
        root_dir=tmp_path,
        ansible=True,
    )

    env_conf = Config.make(
        parsed=parsed,
        pos_args=[],
        source=source,
    ).get_env("insanity-py3.13-2.18")

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(
        buffer=output,
        encoding="utf-8",
        line_buffering=True,
    )

    state = State(
        options=Options(
            parsed=parsed,
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )

    tox_add_env_config(env_conf, state)
    assert not env_conf.loaders
