# Generated with AI assistance: Cursor (xAI)
# ruff: noqa: PLR2004
"""Tests for time-based scenario job bucketing."""

from __future__ import annotations

import io
import json
import logging

from pathlib import Path
from typing import cast

import pytest

from tox.config.cli.parse import Options
from tox.config.cli.parser import Parsed
from tox.config.loader.memory import MemoryLoader  # noqa: TC002
from tox.config.main import Config
from tox.config.sets import CoreConfigSet, EnvConfigSet  # noqa: TC002
from tox.config.source import discover_source
from tox.report import ToxHandler
from tox.session.state import State

from tox_ansible.bucketing import (
    JobMatrix,
    _cli_count,
    _coerce_count,
    _WeightedScenario,
    assign_job,
    build_job_matrix,
    execution_seconds,
    job_scenario_names,
    molecule_scenario_command,
    narrow_impact_report,
    require_integration_targets,
    require_matrix_limits,
    resolve_matrix_limits,
    scenario_seconds,
    split_into_balanced_buckets,
    write_job_matrix,
    write_scenario_matrix,
)
from tox_ansible.impact import ImpactReport
from tox_ansible.plugin import (
    Collection,
    _load_ansible_config,
    conf_commands_for_integration,
    tox_add_core_config,
    tox_add_env_config,
)


def _parsed(**kwargs: object) -> Parsed:
    """Build a tox CLI namespace.

    Args:
        **kwargs: Option overrides.

    Returns:
        The parsed options.
    """
    kwargs.setdefault("override", [])
    kwargs.setdefault("result_json", None)
    return Parsed(**kwargs)


def _option_values(config_file: Path, **overrides: object) -> dict[str, object]:
    """Return CLI values for a config file.

    Args:
        config_file: Tox config file.
        **overrides: CLI option overrides.

    Returns:
        Parsed-option values.
    """
    values: dict[str, object] = {
        "work_dir": config_file.parent / ".tox",
        "config_file": config_file,
        "root_dir": config_file.parent,
        "ansible": True,
        "coverage": None,
        "gh_matrix": False,
        "gh_matrix_jobs": False,
        "matrix_job": "",
        "matrix_jobs": None,
        "matrix_max_parallel": None,
        "impact_file": "",
        "matrix_scope": "all",
    }
    values.update(overrides)
    return values


def _state(config_file: Path, **overrides: object) -> State:
    """Create a tox state for plugin hook tests.

    Args:
        config_file: Tox config file.
        **overrides: CLI option overrides.

    Returns:
        The tox state.
    """
    source = discover_source(config_file, None)
    output = io.BytesIO()
    wrapper = io.TextIOWrapper(output, encoding="utf-8", line_buffering=True)
    return State(
        options=Options(
            parsed=_parsed(**_option_values(config_file, **overrides)),
            pos_args="",
            source=source,
            cmd_handlers={},
            log_handler=ToxHandler(level=0, is_colored=False, out_err=(wrapper, wrapper)),
        ),
        args=[],
    )


def _env(config_file: Path, env_name: str, **overrides: object) -> tuple[EnvConfigSet, State]:
    """Create an env config and matching tox state.

    Args:
        config_file: Tox config file.
        env_name: Tox environment name.
        **overrides: CLI option overrides.

    Returns:
        The environment config and state.
    """
    source = discover_source(config_file, None)
    parsed = _parsed(**_option_values(config_file, **overrides))
    output = io.BytesIO()
    wrapper = io.TextIOWrapper(output, encoding="utf-8", line_buffering=True)
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
    env_conf = Config.make(
        parsed=parsed,
        pos_args=[],
        source=source,
        extra_envs=[],
    ).get_env(env_name)
    env_conf.add_config(
        keys=["env_dir", "envdir"],
        of_type=Path,
        default=config_file.parent,
        desc="",
    )
    return env_conf, state


def _write_project(project_dir: Path) -> Path:
    """Write a collection with two integration targets and one molecule scenario.

    Args:
        project_dir: Project root.

    Returns:
        The tox config path.
    """
    (project_dir / "galaxy.yml").write_text(
        "namespace: test\nname: test\nversion: 1.0.0\n",
        encoding="utf-8",
    )
    slow = project_dir / "tests" / "integration" / "targets" / "slow_target"
    fast = project_dir / "tests" / "integration" / "targets" / "fast_target"
    slow.mkdir(parents=True)
    fast.mkdir(parents=True)
    (slow / "aliases").write_text("slow\n", encoding="utf-8")
    (fast / "aliases").write_text("time=10\n", encoding="utf-8")
    scenario = project_dir / "extensions" / "molecule" / "default"
    scenario.mkdir(parents=True)
    (scenario / "molecule.yml").write_text("", encoding="utf-8")
    (project_dir / "impact.json").write_text(
        json.dumps(
            {
                "collection": "test.test",
                "integration_targets": [
                    "tests/integration/targets/slow_target",
                    "tests/integration/targets/fast_target",
                ],
                "molecule_scenarios": ["extensions/molecule/default"],
            },
        ),
        encoding="utf-8",
    )
    config_file = project_dir / "tox-ansible.ini"
    config_file.write_text(
        "[ansible]\nimpact_file = impact.json\nmatrix_jobs = 2\nmatrix_max_parallel = 4\n",
        encoding="utf-8",
    )
    return config_file


def _assert_partition(matrix: JobMatrix, names: set[str]) -> None:
    """Assert every name is assigned to exactly one job.

    Args:
        matrix: Matrix under test.
        names: Scenario names that must be assigned.
    """
    assigned: list[str] = []
    for job_id in matrix.jobs:
        assigned.extend(matrix.scenarios[job_id].split())
    assert len(assigned) == len(set(assigned))
    assert set(assigned) == names


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("", 180),
        ("slow\n", 3000),
        ("time=45s\n", 45),
        ("time=2m\n", 120),
        ("time=45\n", 45),
        ("slow\ntime=10\n", 10),
        ("# comment\n\ncloud\ntime=30s # note\n", 30),
        ("time=5\ntime=9s\n", 9),
    ),
)
def test_execution_seconds(text: str, expected: int) -> None:
    """Test aliases duration parsing.

    Args:
        text: Aliases file text.
        expected: Expected seconds.
    """
    assert execution_seconds(text) == expected


def test_scenario_seconds_defaults_and_aliases(tmp_path: Path) -> None:
    """Test duration lookup for molecule, missing aliases, and a time alias.

    Args:
        tmp_path: Pytest fixture.
    """
    assert scenario_seconds(tmp_path, "molecule", "default") == 180
    assert scenario_seconds(tmp_path, "integration", "missing") == 180
    alias = tmp_path / "tests" / "integration" / "targets" / "demo" / "aliases"
    alias.parent.mkdir(parents=True)
    alias.write_text("time=12\n", encoding="utf-8")
    assert scenario_seconds(tmp_path, "integration", "demo") == 12


def test_scenario_seconds_unreadable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a default duration when the aliases file cannot be read.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
        caplog: Pytest fixture.
    """
    alias = tmp_path / "tests" / "integration" / "targets" / "demo" / "aliases"
    alias.parent.mkdir(parents=True)
    alias.write_bytes(b"\xff")
    caplog.set_level(logging.WARNING)
    assert scenario_seconds(tmp_path, "integration", "demo") == 180
    assert "Cannot read aliases" in caplog.text

    alias.write_text("time=10\n", encoding="utf-8")

    def _boom(*_args: object, **_kwargs: object) -> str:
        message = "denied"
        raise OSError(message)

    monkeypatch.setattr(Path, "read_text", _boom)
    assert scenario_seconds(tmp_path, "integration", "demo") == 180


def test_split_edges() -> None:
    """Test empty input, a bad job count, and overflow into the first job."""
    with pytest.raises(ValueError, match="positive"):
        split_into_balanced_buckets([], 0)
    assert split_into_balanced_buckets([], 2) == []

    small = [_WeightedScenario(name, 10) for name in ("a", "b", "c")]
    assert split_into_balanced_buckets(small, 2) == [["a", "c"], ["b"]]

    large = [_WeightedScenario(name, 1000) for name in ("a", "b", "c")]
    assert split_into_balanced_buckets(large, 2) == [["a", "c"], ["b"]]

    two_large = [_WeightedScenario("a", 50), _WeightedScenario("b", 50), _WeightedScenario("c", 10)]
    assert split_into_balanced_buckets(two_large, 3) == [["a"], ["b"], ["c"]]

    single = [_WeightedScenario("only", 180)]
    assert split_into_balanced_buckets(single, 3) == [["only"]]


def test_build_job_matrix_packs_by_time_and_kind(tmp_path: Path) -> None:
    """Test separate integration and molecule buckets.

    Args:
        tmp_path: Pytest fixture.
    """
    _write_project(tmp_path)
    report = ImpactReport(
        collection="test.test",
        integration_targets=[
            "tests/integration/targets/fast_target",
            "tests/integration/targets/slow_target",
            "tests/integration/targets/slow_target",
        ],
        molecule_scenarios=["extensions/molecule/default"],
    )
    matrix = build_job_matrix(report, tmp_path, job_count=2, max_parallel=4)
    assert matrix.jobs == ["integration-1", "integration-2", "molecule-1"]
    assert matrix.scenarios == {
        "integration-1": "slow_target",
        "integration-2": "fast_target",
        "molecule-1": "extensions/molecule/default",
    }
    assert matrix.max_parallel == 4
    _assert_partition(matrix, {"slow_target", "fast_target", "extensions/molecule/default"})


def test_build_job_matrix_tie_breaks_by_name(tmp_path: Path) -> None:
    """Test equal estimates are ordered by scenario name.

    Args:
        tmp_path: Pytest fixture.
    """
    report = ImpactReport(
        collection="test.test",
        integration_targets=[
            "tests/integration/targets/b",
            "tests/integration/targets/a",
        ],
    )
    matrix = build_job_matrix(report, tmp_path, job_count=2, max_parallel=None)
    assert matrix.scenarios == {"integration-1": "a", "integration-2": "b"}
    assert matrix.as_dict() == {
        "jobs": ["integration-1", "integration-2"],
        "scenarios": matrix.scenarios,
    }


def test_job_ids_and_narrow() -> None:
    """Test job lookup and narrowing a report to one job."""
    report = ImpactReport(
        collection="test.test",
        integration_targets=[
            "tests/integration/targets/a",
            "tests/integration/targets/a",
            "tests/integration/targets/b",
        ],
        molecule_scenarios=["extensions/molecule/default"],
    )
    matrix = JobMatrix(jobs=["integration-1"], scenarios={"integration-1": "a b"})
    assert job_scenario_names(matrix, "integration-1") == ["a", "b"]
    with pytest.raises(ValueError, match="Unknown matrix job 'nope'"):
        job_scenario_names(matrix, "nope")
    with pytest.raises(ValueError, match="Known jobs"):
        job_scenario_names(matrix, "integration-2")

    integration = narrow_impact_report(report, "integration-1", ["b", "missing", "a"])
    assert integration.integration_targets == [
        "tests/integration/targets/b",
        "tests/integration/targets/a",
    ]
    assert not integration.molecule_scenarios
    molecule = narrow_impact_report(report, "molecule-1", ["extensions/molecule/default"])
    assert molecule.molecule_scenarios == ["extensions/molecule/default"]
    assert not molecule.integration_targets
    with pytest.raises(ValueError, match="Invalid matrix job"):
        narrow_impact_report(report, "nope", [])
    with pytest.raises(ValueError, match="Invalid matrix job"):
        narrow_impact_report(report, "sanity-1", [])


def test_build_job_matrix_keeps_duplicate_molecule_basenames(tmp_path: Path) -> None:
    """Molecule scenarios that share a directory name stay distinct.

    Args:
        tmp_path: Pytest fixture.
    """
    report = ImpactReport(
        collection="test.test",
        molecule_scenarios=[
            "extensions/molecule/default",
            "roles/example/molecule/default",
            "extensions/molecule/default",
        ],
    )
    matrix = build_job_matrix(report, tmp_path, job_count=2, max_parallel=None)
    assigned = " ".join(matrix.scenarios[job] for job in matrix.jobs).split()
    assert assigned.count("extensions/molecule/default") == 1
    assert assigned.count("roles/example/molecule/default") == 1
    narrowed = narrow_impact_report(
        report,
        "molecule-1",
        ["roles/example/molecule/default"],
    )
    assert narrowed.molecule_scenarios == ["roles/example/molecule/default"]


@pytest.mark.parametrize(
    ("scenario_path", "expected"),
    (
        ("default", "python3 -m molecule test -s default"),
        ("extensions/molecule/default", "python3 -m molecule test -s default"),
        (
            "extensions/molecule/appliance_vlans/merged",
            "python3 -m molecule test -s appliance_vlans/merged",
        ),
        ("extensions/molecule", "python3 -m molecule test -s default"),
        (
            "roles/example/molecule/default",
            "bash -c 'cd roles/example && python3 -m molecule test -s default'",
        ),
        (
            "roles/example/molecule",
            "bash -c 'cd roles/example && python3 -m molecule test -s default'",
        ),
        ("molecule/default", "python3 -m molecule test -s default"),
        ("molecule/group/merged", "python3 -m molecule test -s merged"),
        ("molecule", "python3 -m molecule test -s default"),
    ),
)
def test_molecule_scenario_command(scenario_path: str, expected: str) -> None:
    """Molecule commands use -s, and role layouts cd to the molecule parent.

    Args:
        scenario_path: Impact-report scenario path.
        expected: Command that must be produced.
    """
    assert molecule_scenario_command(scenario_path, None, None) == expected


def test_build_job_matrix_rejects_whitespace_ids(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A space in a scenario id cannot survive the space-separated matrix.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture.
    """
    report = ImpactReport(
        collection="test.test",
        molecule_scenarios=["roles/my role/molecule/default"],
    )
    caplog.set_level(logging.CRITICAL)
    with pytest.raises(SystemExit) as exc:
        build_job_matrix(report, tmp_path, job_count=1, max_parallel=None)
    assert exc.value.code == 1
    assert "cannot contain whitespace" in caplog.text
    assert "roles/my role/molecule/default" in caplog.text


def test_assign_job(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test selecting one job and rejecting an unknown job id.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture.
    """
    report = ImpactReport(
        collection="test.test",
        integration_targets=["tests/integration/targets/a"],
    )
    (tmp_path / "tests" / "integration" / "targets" / "a").mkdir(parents=True)
    assigned = assign_job(report, tmp_path, 1, None, "integration-1")
    assert assigned.integration_targets == ["tests/integration/targets/a"]
    caplog.set_level(logging.CRITICAL)
    with pytest.raises(SystemExit) as exc:
        assign_job(report, tmp_path, 1, None, "integration-9")
    assert exc.value.code == 1
    assert "Unknown matrix job 'integration-9'" in caplog.text


def test_assign_job_rejects_missing_integration_target(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing target dirs must fail before matrix rebuild can reshuffle jobs.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture.
    """
    (tmp_path / "tests" / "integration" / "targets" / "b").mkdir(parents=True)
    report = ImpactReport(
        collection="test.test",
        integration_targets=[
            "tests/integration/targets/a",
            "tests/integration/targets/b",
        ],
    )
    caplog.set_level(logging.CRITICAL)
    with pytest.raises(SystemExit) as exc:
        assign_job(report, tmp_path, 2, None, "integration-1")
    assert exc.value.code == 1
    assert "not found under" in caplog.text
    assert "a" in caplog.text


def test_require_integration_targets_noop_without_targets(tmp_path: Path) -> None:
    """Molecule-only reports skip integration target checks.

    Args:
        tmp_path: Pytest fixture.
    """
    report = ImpactReport(
        collection="test.test",
        molecule_scenarios=["extensions/molecule/default"],
    )
    require_integration_targets(report, tmp_path)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (None, 0),
        (True, 0),
        (4, 4),
        ("8", 8),
        (" -3 ", -3),
        ("nope", 0),
        (1.5, 0),
    ),
)
def test_coerce_count(value: object, expected: int) -> None:
    """Test integer coercion for config values.

    Args:
        value: Raw config value.
        expected: Coerced integer.
    """
    assert _coerce_count(value) == expected


def test_cli_count_rejects_non_integers() -> None:
    """Test CLI values that are not integers."""
    assert _cli_count(None, "--matrix-jobs") is None
    assert _cli_count("", "--matrix-jobs") is None
    assert _cli_count(6, "--matrix-jobs") == 6
    assert _cli_count("4", "--matrix-max-parallel") == 4
    not_an_int = True
    with pytest.raises(SystemExit):
        _cli_count(not_an_int, "--matrix-jobs")
    with pytest.raises(SystemExit):
        _cli_count("nope", "--matrix-max-parallel")
    with pytest.raises(SystemExit):
        _cli_count(1.5, "--matrix-jobs")


def test_resolve_and_require_limits() -> None:
    """Test config/CLI precedence and validation of job limits."""
    assert resolve_matrix_limits(4, 0, None, None) == (4, None)
    assert resolve_matrix_limits(4, 8, None, None) == (4, 8)
    assert resolve_matrix_limits(4, 8, 2, None) == (2, 8)
    assert resolve_matrix_limits(4, 8, None, 3) == (4, 3)
    assert resolve_matrix_limits(4, 8, None, 0) == (4, 0)
    assert require_matrix_limits(2, None) == (2, None)
    assert require_matrix_limits(2, 3) == (2, 3)
    with pytest.raises(SystemExit):
        require_matrix_limits(0, None)
    with pytest.raises(SystemExit):
        require_matrix_limits(2, 0)


def test_load_matrix_limits_from_ini_toml_and_cli(tmp_path: Path) -> None:
    """Test matrix settings from INI, TOML, and the CLI.

    Args:
        tmp_path: Pytest fixture.
    """
    ini = tmp_path / "tox-ansible.ini"
    ini.write_text("[ansible]\nmatrix_jobs = 4\n", encoding="utf-8")
    from_ini = _load_ansible_config(_state(ini))
    assert from_ini.matrix_jobs == 4
    assert from_ini.matrix_max_parallel is None

    (tmp_path / "pyproject.toml").write_text(
        "[tool.tox-ansible]\nmatrix_jobs = 5\nmatrix_max_parallel = 2\n",
        encoding="utf-8",
    )
    from_toml = _load_ansible_config(_state(ini, matrix_jobs=9))
    assert from_toml.matrix_jobs == 9
    assert from_toml.matrix_max_parallel == 2
    from_cli_parallel = _load_ansible_config(_state(ini, matrix_max_parallel=7))
    assert from_cli_parallel.matrix_jobs == 5
    assert from_cli_parallel.matrix_max_parallel == 7
    bad_state = _state(ini, matrix_jobs=True)
    with pytest.raises(SystemExit):
        _load_ansible_config(bad_state)


def test_write_job_matrix_stdout_and_github_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test stdout and GITHUB_OUTPUT publication.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
        capsys: Pytest fixture.
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    plain = JobMatrix(jobs=["integration-1"], scenarios={"integration-1": "a"})
    write_job_matrix(plain)
    assert json.loads(capsys.readouterr().out) == plain.as_dict()

    output = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    write_job_matrix(
        JobMatrix(jobs=["integration-1"], scenarios={"integration-1": "a"}, max_parallel=2),
    )
    text = output.read_text(encoding="utf-8")
    assert 'jobs=["integration-1"]\n' in text
    assert 'scenarios={"integration-1": "a"}\n' in text
    assert "max_parallel=2\n" in text

    monkeypatch.delenv("GITHUB_OUTPUT")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with pytest.raises(SystemExit) as exc:
        write_job_matrix(plain)
    assert exc.value.code == 1


def test_write_job_matrix_multiline_github_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the heredoc GITHUB_OUTPUT form when a value contains a newline.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    output = tmp_path / "github_output.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    original = json.dumps

    def _dumps(obj: object, *_args: object, **_kwargs: object) -> str:
        return original(obj) + "\n"

    monkeypatch.setattr("tox_ansible.bucketing.json.dumps", _dumps)
    write_job_matrix(JobMatrix(jobs=["integration-1"], scenarios={"integration-1": "a"}))
    text = output.read_text(encoding="utf-8")
    assert "jobs<<EOF-" in text
    assert "scenarios<<EOF-" in text
    assert "max_parallel" not in text


def test_write_scenario_matrix_requires_file_and_positive_limits(tmp_path: Path) -> None:
    """Test matrix publication rejects a missing file and non-positive limits.

    Args:
        tmp_path: Pytest fixture.
    """
    collection = Collection(name="test", namespace="test", version="1.0.0")
    with pytest.raises(SystemExit):
        write_scenario_matrix(tmp_path, None, 2, None, collection)
    with pytest.raises(SystemExit):
        write_scenario_matrix(tmp_path, "impact.json", 0, None, collection)
    with pytest.raises(SystemExit):
        write_scenario_matrix(tmp_path, "impact.json", 2, 0, collection)


def test_gh_matrix_jobs_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --gh-matrix-jobs output from the tox hook.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
        capsys: Pytest fixture.
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    config_file = _write_project(tmp_path)
    state = _state(config_file, gh_matrix_jobs=True)
    with pytest.raises(SystemExit) as exc:
        tox_add_core_config(cast("CoreConfigSet", None), state)
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["jobs"] == ["integration-1", "integration-2", "molecule-1"]
    assert payload["scenarios"]["integration-1"] == "slow_target"
    assert payload["scenarios"]["integration-2"] == "fast_target"
    assert payload["scenarios"]["molecule-1"] == "extensions/molecule/default"
    assert payload["max_parallel"] == 4
    assigned = " ".join(payload["scenarios"].values()).split()
    assert sorted(assigned) == ["extensions/molecule/default", "fast_target", "slow_target"]


@pytest.mark.parametrize(
    ("overrides", "flag"),
    (
        ({"gh_matrix": True}, "--gh-matrix"),
        ({"gh_matrix_jobs": True}, "--gh-matrix-jobs"),
        ({"matrix_job": "integration-1"}, "--matrix-job"),
        ({"coverage": True}, "--coverage"),
    ),
)
def test_matrix_flags_require_ansible(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    overrides: dict[str, object],
    flag: str,
) -> None:
    """Test ansible is required for matrix and coverage flags.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture.
        overrides: CLI overrides.
        flag: Flag named in the error.
    """
    config_file = tmp_path / "tox-ansible.ini"
    config_file.write_text("[ansible]\n", encoding="utf-8")
    caplog.set_level(logging.CRITICAL)
    state = _state(config_file, ansible=False, **overrides)
    with pytest.raises(SystemExit) as exc:
        tox_add_core_config(cast("CoreConfigSet", None), state)
    assert exc.value.code == 1
    assert f"The {flag} option requires --ansible" in caplog.text


def test_core_config_without_matrix_flags(tmp_path: Path) -> None:
    """Test tox config continues when scenario bucketing is not requested.

    Args:
        tmp_path: Pytest fixture.
    """
    config_file = tmp_path / "tox-ansible.ini"
    config_file.write_text("[ansible]\n", encoding="utf-8")
    assert tox_add_core_config(cast("CoreConfigSet", None), _state(config_file)) is None
    assert (
        tox_add_core_config(
            cast("CoreConfigSet", None),
            _state(config_file, ansible=False),
        )
        is None
    )


def test_gh_matrix_and_gh_matrix_jobs_conflict(tmp_path: Path) -> None:
    """Test the two matrix emitters cannot be combined.

    Args:
        tmp_path: Pytest fixture.
    """
    config_file = tmp_path / "tox-ansible.ini"
    config_file.write_text("[ansible]\n", encoding="utf-8")
    state = _state(config_file, gh_matrix=True, gh_matrix_jobs=True)
    with pytest.raises(SystemExit) as exc:
        tox_add_core_config(cast("CoreConfigSet", None), state)
    assert exc.value.code == 1


def test_gh_matrix_still_lists_environments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --gh-matrix still prints the tox environment list.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
        capsys: Pytest fixture.
    """
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    config_file = tmp_path / "tox-ansible.ini"
    config_file.write_text("[ansible]\n", encoding="utf-8")
    state = _state(config_file, gh_matrix=True)
    with pytest.raises(SystemExit) as exc:
        tox_add_core_config(cast("CoreConfigSet", None), state)
    assert exc.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert payload[0]["name"]


def test_matrix_job_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test one job runs only its scenarios and the other kind is skipped.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
        caplog: Pytest fixture.
    """
    monkeypatch.chdir(tmp_path)
    config_file = _write_project(tmp_path)
    caplog.set_level(logging.WARNING)
    integration_env, integration_state = _env(
        config_file,
        "integration-py3.14-2.19",
        matrix_job="integration-1",
    )
    tox_add_env_config(integration_env, integration_state)
    integration_commands = cast("MemoryLoader", integration_env.loaders[0]).raw["commands"]
    assert any("slow_target" in command for command in integration_commands)
    assert all("fast_target" not in command for command in integration_commands)

    molecule_env, molecule_state = _env(
        config_file,
        "molecule-py3.14-2.19",
        matrix_job="molecule-1",
    )
    tox_add_env_config(molecule_env, molecule_state)
    molecule_commands = cast("MemoryLoader", molecule_env.loaders[0]).raw["commands"]
    assert any("-s default" in command for command in molecule_commands)

    skipped_env, skipped_state = _env(
        config_file,
        "molecule-py3.14-2.19",
        matrix_job="integration-1",
    )
    tox_add_env_config(skipped_env, skipped_state)
    skipped = cast("MemoryLoader", skipped_env.loaders[0]).raw["commands"]
    assert skipped == ["echo skipping molecule for --matrix-job integration-1"]
    assert "selects integration scenarios" in caplog.text


def test_matrix_job_requires_impact_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --matrix-job without an impact file exits.

    Args:
        tmp_path: Pytest fixture.
        monkeypatch: Pytest fixture.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "galaxy.yml").write_text(
        "namespace: test\nname: test\nversion: 1.0.0\n",
        encoding="utf-8",
    )
    config_file = tmp_path / "tox-ansible.ini"
    config_file.write_text("[ansible]\nmatrix_jobs = 2\n", encoding="utf-8")
    env_conf, state = _env(config_file, "integration-py3.14-2.19", matrix_job="integration-1")
    with pytest.raises(SystemExit) as exc:
        tox_add_env_config(env_conf, state)
    assert exc.value.code == 1


def test_matrix_job_command_edges(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test strict integration scope when a matrix job is selected.

    Args:
        tmp_path: Pytest fixture.
        caplog: Pytest fixture.
    """
    config_file = tmp_path / "tox-ansible.ini"
    config_file.write_text("[ansible]\n", encoding="utf-8")
    env_conf, _ = _env(config_file, "integration-py3.14-2.19")
    collection = Collection(name="test", namespace="test", version="1.0.0")

    with pytest.raises(SystemExit) as empty_scope:
        conf_commands_for_integration(
            collection=collection,
            env_conf=env_conf,
            pos_args=None,
            project_dir=tmp_path,
            impact_report=ImpactReport(collection="test.test"),
            strict_scope=True,
        )
    assert empty_scope.value.code == 1
    assert "Matrix job has no integration targets to run" in caplog.text

    with pytest.raises(SystemExit) as missing_scope:
        conf_commands_for_integration(
            collection=collection,
            env_conf=env_conf,
            pos_args=None,
            project_dir=tmp_path,
            impact_report=ImpactReport(
                collection="test.test",
                integration_targets=["tests/integration/targets/missing"],
            ),
            strict_scope=True,
        )
    assert missing_scope.value.code == 1
    assert "Assigned integration targets not found" in caplog.text

    present = tmp_path / "tests" / "integration" / "targets" / "present"
    present.mkdir(parents=True)
    with pytest.raises(SystemExit) as partial_scope:
        conf_commands_for_integration(
            collection=collection,
            env_conf=env_conf,
            pos_args=None,
            project_dir=tmp_path,
            impact_report=ImpactReport(
                collection="test.test",
                integration_targets=[
                    "tests/integration/targets/present",
                    "tests/integration/targets/missing",
                ],
            ),
            strict_scope=True,
        )
    assert partial_scope.value.code == 1
    assert "missing" in caplog.text
