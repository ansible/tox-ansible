"""Time-based CI job buckets for impact-selected scenarios.

Packs integration targets and molecule scenarios the same way
``ansible_test_splitter`` packs targets: sort by estimated seconds, then fill
jobs up to an equal share of the total. Integration times come from ansible-test
``aliases`` files. Molecule scenarios use the default duration.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import sys
import uuid

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from tox_ansible.impact import ImpactReport, load_impact_report


if TYPE_CHECKING:
    from tox_ansible.plugin import Collection

logger = logging.getLogger(__name__)

DEFAULT_SECONDS = 180
SLOW_SECONDS = 3000
_TIME_SECONDS = re.compile(r"^time=(\d+)s\S*$")
_TIME_MINUTES = re.compile(r"^time=(\d+)m\S*$")
# Digits and the suffix are disjoint so the match cannot backtrack.
_TIME_BARE = re.compile(r"^time=(\d+)(?:[^\d\s]\S*)?$")
_JOB_ID = re.compile(r"^(integration|molecule)-[1-9]\d*$")


@dataclass(frozen=True)
class JobMatrix:
    """GitHub Actions matrix that assigns each scenario to one job.

    Attributes:
        jobs: Job ids such as ``integration-1`` or ``molecule-2``.
        scenarios: Map of job id to a space-separated scenario list.
        max_parallel: Optional cap for the workflow ``max-parallel`` setting.
    """

    jobs: list[str]
    scenarios: dict[str, str]
    max_parallel: int | None = None

    def as_dict(self) -> dict[str, object]:
        """Return the JSON object printed for ``--gh-matrix-jobs``.

        Returns:
            Matrix payload. ``max_parallel`` is omitted when unset.
        """
        payload: dict[str, object] = {"jobs": list(self.jobs), "scenarios": dict(self.scenarios)}
        if self.max_parallel is not None:
            payload["max_parallel"] = self.max_parallel
        return payload


@dataclass(frozen=True)
class _WeightedScenario:
    """One scenario and its estimated runtime.

    Attributes:
        name: Scenario or target name passed to the test command.
        seconds: Estimated runtime in seconds.
    """

    name: str
    seconds: int


@dataclass
class _Bucket:
    """One in-progress job bucket.

    Attributes:
        total: Sum of estimated seconds assigned to the bucket.
        names: Scenario names assigned to the bucket.
    """

    total: int = 0
    names: list[str] = field(default_factory=list)


def execution_seconds(aliases_text: str) -> int:
    """Estimate runtime from an ansible-test aliases file.

    ``time=`` aliases replace the default. A ``slow`` alias uses 3000 seconds
    when no ``time=`` alias is present. The last ``time=`` line wins.

    Args:
        aliases_text: Aliases file contents.

    Returns:
        Estimated runtime in seconds.
    """
    seconds = DEFAULT_SECONDS
    saw_slow = False
    timed = False
    for raw in aliases_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line == "slow":
            saw_slow = True
        if match := _TIME_MINUTES.match(line):
            seconds = int(match.group(1)) * 60
            timed = True
        elif match := _TIME_SECONDS.match(line) or _TIME_BARE.match(line):
            seconds = int(match.group(1))
            timed = True
    if saw_slow and not timed:
        return SLOW_SECONDS
    return seconds


def scenario_seconds(
    project_dir: Path,
    kind: str,
    name: str,
    *,
    strict: bool = False,
) -> int:
    """Return the estimated seconds for one scenario.

    Args:
        project_dir: Collection root.
        kind: ``integration`` or ``molecule``.
        name: Target or scenario name.
        strict: When ``True``, unreadable aliases files exit instead of defaulting.
            Missing files still use the default in either mode.

    Returns:
        Estimated runtime in seconds.
    """
    if kind != "integration":
        return DEFAULT_SECONDS
    alias_path = project_dir / "tests" / "integration" / "targets" / name / "aliases"
    try:
        text = alias_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return DEFAULT_SECONDS
    except (OSError, UnicodeError):
        if strict:
            logger.critical(
                "Cannot read aliases for integration target %s at %s",
                name,
                alias_path,
            )
            sys.exit(1)
        logger.warning(
            "Cannot read aliases for integration target %s; using %ss",
            name,
            DEFAULT_SECONDS,
        )
        return DEFAULT_SECONDS
    return execution_seconds(text)


def _find_slot(
    item: _WeightedScenario,
    chunks: list[_Bucket],
    time_per_chunk: int,
) -> int:
    """Return the bucket index for one scenario.

    A scenario at least as long as one share takes the first empty bucket.
    A shorter scenario takes the first bucket that can hold it. Otherwise it
    goes in the first bucket.

    Args:
        item: Scenario to place.
        chunks: Buckets filled so far.
        time_per_chunk: Equal share of the total runtime, in seconds.

    Returns:
        Index of the chosen bucket.
    """
    if item.seconds >= time_per_chunk:
        for index, chunk in enumerate(chunks):
            if chunk.total == 0:
                return index
        return 0  # pragma: no cover
    for index, chunk in enumerate(chunks):
        if item.seconds + chunk.total <= time_per_chunk:
            return index
    return 0


def split_into_balanced_buckets(
    scenarios: list[_WeightedScenario],
    job_count: int,
) -> list[list[str]]:
    """Pack scenarios into jobs by estimated runtime.

    This follows ``split_into_equally_sized_chunks`` in ansible_test_splitter.
    Scenarios must already be sorted by time, longest first. Empty jobs are
    omitted. When a scenario fits nowhere else, it is placed in the first job.

    Args:
        scenarios: Scenarios sorted by descending seconds, then name.
        job_count: Maximum number of jobs.

    Returns:
        Non-empty name lists, in job order.

    Raises:
        ValueError: ``job_count`` is less than 1.
    """
    if job_count < 1:
        msg = f"job_count must be positive, got {job_count}"
        raise ValueError(msg)
    if not scenarios:
        return []

    total_time = sum(item.seconds for item in scenarios)
    time_per_chunk = int(total_time / job_count) + 1
    chunks = [_Bucket() for _ in range(job_count)]
    for item in scenarios:
        slot = _find_slot(item, chunks, time_per_chunk)
        chunks[slot].total += item.seconds
        chunks[slot].names.append(item.name)
    return [chunk.names for chunk in chunks if chunk.names]


def _scenario_ids(paths: list[str], kind: str) -> list[str]:
    """Return unique scenario ids in first-seen order.

    Integration uses the target directory name. Molecule keeps the impact-report
    path so two scenarios that share a directory name stay distinct.

    Args:
        paths: Impact-report paths or names.
        kind: ``integration`` or ``molecule``.

    Returns:
        Unique scenario ids.
    """
    seen: set[str] = set()
    names: list[str] = []
    for path in paths:
        name = Path(path).name if kind == "integration" else path
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _reject_ambiguous_molecule_commands(paths: list[str]) -> None:
    """Exit when two impact paths would run the same Molecule command.

    Args:
        paths: Molecule scenario paths from the impact report.
    """
    seen: dict[tuple[str | None, str], str] = {}
    for path in paths:
        project, scenario = _molecule_target(path)
        key = (project, scenario)
        prior = seen.get(key)
        if prior is not None and prior != path:
            logger.critical(
                "Molecule scenarios %r and %r run the same command (project=%r, -s=%r)",
                prior,
                path,
                project,
                scenario,
            )
            sys.exit(1)
        seen[key] = path


def _reject_whitespace_ids(names: list[str]) -> None:
    """Exit when a scenario id cannot survive a space-separated matrix value.

    Args:
        names: Scenario ids about to be packed into one job kind.
    """
    spaced = [name for name in names if any(char.isspace() for char in name)]
    if not spaced:
        return
    logger.critical(
        "Scenario ids cannot contain whitespace; matrix jobs are space-separated: %s",
        ", ".join(repr(name) for name in spaced),
    )
    sys.exit(1)


def molecule_scenario_command(
    scenario_path: str,
    molecule_append: list[str] | None,
    pos_args: tuple[str, ...] | None,
) -> str:
    """Build one molecule command for an impact-report scenario path.

    Collection scenarios under ``extensions/molecule/`` use ``molecule test -s``
    with the path relative to that directory. Molecule has no project-directory
    option, so every other scenario runs from the directory that contains
    ``molecule/`` via ``bash -c``.

    Args:
        scenario_path: Scenario path or name from the impact report.
        molecule_append: Extra argv appended to the command.
        pos_args: Positional arguments passed to tox.

    Returns:
        A command that runs that scenario.
    """
    project, scenario = _molecule_target(scenario_path)
    argv = ["python3", "-m", "molecule", "test", "-s", scenario]
    if molecule_append:
        argv.extend(molecule_append)
    if pos_args:
        argv.extend(pos_args)
    command = " ".join(shlex.quote(part) for part in argv)
    if project is None:
        return command
    script = f"cd {shlex.quote(project)} && {command}"
    return f"bash -c {shlex.quote(script)}"


def _molecule_target(scenario_path: str) -> tuple[str | None, str]:
    """Return the working directory and ``-s`` name for one scenario path.

    Args:
        scenario_path: Scenario path or name from the impact report.

    Returns:
        Project directory, or None to stay at the collection root, and the
        scenario name Molecule accepts.
    """
    normalized = scenario_path.replace("\\", "/").strip("/")
    parts = tuple(part for part in normalized.split("/") if part not in {"", "."})
    if "molecule" not in parts:
        return None, normalized
    marker = len(parts) - 1 - parts[::-1].index("molecule")
    project = parts[:marker]
    rest = parts[marker + 1 :]
    scenario = "/".join(rest) if rest else "default"
    if project == ("extensions",):
        return None, scenario
    if not project:
        return None, scenario
    return "/".join(project), scenario


def require_integration_targets(report: ImpactReport, project_dir: Path) -> None:
    """Exit when the report names integration targets that are not on disk.

    ``build_job_matrix`` estimates missing targets at the default duration, which
    can change job assignments relative to a full checkout.

    Args:
        report: Impact report listing integration target paths.
        project_dir: Collection root.
    """
    if not report.integration_targets:
        return
    targets_dir = project_dir / "tests" / "integration" / "targets"
    missing = [
        name
        for name in _scenario_ids(report.integration_targets, "integration")
        if not (targets_dir / name).is_dir()
    ]
    if missing:
        logger.critical(
            "Integration targets from impact report not found under %s: %s",
            targets_dir,
            ", ".join(missing),
        )
        sys.exit(1)


def build_job_matrix(
    report: ImpactReport,
    project_dir: Path,
    job_count: int,
    max_parallel: int | None,
) -> JobMatrix:
    """Build a job matrix for integration targets and molecule scenarios.

    The two kinds are packed separately so a job runs only one command type.
    Equal estimates break ties by scenario name.

    Args:
        report: Selected scenarios.
        project_dir: Collection root, used to read aliases files.
        job_count: Maximum jobs for each kind.
        max_parallel: Workflow cap, or None to omit it.

    Returns:
        The job matrix. Kinds with no scenarios contribute no jobs.
    """
    jobs: list[str] = []
    scenarios: dict[str, str] = {}
    groups = (
        ("integration", report.integration_targets),
        ("molecule", report.molecule_scenarios),
    )
    for kind, paths in groups:
        names = _scenario_ids(paths, kind)
        _reject_whitespace_ids(names)
        if kind == "molecule":
            _reject_ambiguous_molecule_commands(names)
        weighted = [
            _WeightedScenario(name, scenario_seconds(project_dir, kind, name, strict=True))
            for name in names
        ]
        weighted.sort(key=lambda item: (-item.seconds, item.name))
        buckets = split_into_balanced_buckets(weighted, job_count)
        for index, names in enumerate(buckets, start=1):
            job_id = f"{kind}-{index}"
            jobs.append(job_id)
            scenarios[job_id] = " ".join(names)
    return JobMatrix(jobs=jobs, scenarios=scenarios, max_parallel=max_parallel)


def job_scenario_names(matrix: JobMatrix, job_id: str) -> list[str]:
    """Return the scenario names assigned to one job.

    Args:
        matrix: Matrix from :func:`build_job_matrix`.
        job_id: Job id such as ``integration-1``.

    Returns:
        Scenario names in bucket order.

    Raises:
        ValueError: The job id is unknown or malformed.
    """
    if _JOB_ID.fullmatch(job_id) is None or job_id not in matrix.scenarios:
        known = ", ".join(matrix.jobs) if matrix.jobs else "(none)"
        msg = f"Unknown matrix job '{job_id}'. Known jobs: {known}"
        raise ValueError(msg)
    return matrix.scenarios[job_id].split()


def narrow_impact_report(report: ImpactReport, job_id: str, names: list[str]) -> ImpactReport:
    """Keep only the scenarios assigned to one job.

    Args:
        report: Full impact report.
        job_id: Job id. The prefix selects integration or molecule.
        names: Scenario names assigned to the job.

    Returns:
        Copy of the report containing that job's scenarios.

    Raises:
        ValueError: ``job_id`` does not name an integration or molecule job.
    """
    kind, separator, _index = job_id.partition("-")
    if separator != "-" or kind not in {"integration", "molecule"}:
        msg = f"Invalid matrix job id '{job_id}'"
        raise ValueError(msg)
    order = {name: index for index, name in enumerate(names)}
    chosen: dict[str, str] = {}
    paths = report.integration_targets if kind == "integration" else report.molecule_scenarios
    for path in paths:
        name = Path(path).name if kind == "integration" else path
        if name in order and name not in chosen:
            chosen[name] = path
    ordered = [chosen[name] for name in names if name in chosen]
    if kind == "integration":
        integration_targets = ordered
        molecule_scenarios: list[str] = []
    else:
        integration_targets = []
        molecule_scenarios = ordered
    return ImpactReport(
        collection=report.collection,
        changed_files=list(report.changed_files),
        affected_plugins=list(report.affected_plugins),
        molecule_scenarios=molecule_scenarios,
        integration_targets=integration_targets,
        reasons=dict(report.reasons),
    )


def _coerce_count(value: object, *, default: int = 0) -> int:
    """Coerce a config value to an integer.

    Args:
        value: Raw TOML or INI value.
        default: Fallback when the value cannot be interpreted.

    Returns:
        The coerced integer.
    """
    if isinstance(value, bool) or value is None:
        if value is not None:
            logger.warning("Invalid integer config value %r; using %s", value, default)
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    logger.warning("Invalid integer config value %r; using %s", value, default)
    return default


def _exit_not_integer(option: str) -> NoReturn:
    """Reject a CLI value that is not an integer.

    Args:
        option: Option name used in the error.
    """
    logger.critical("%s must be an integer", option)
    sys.exit(1)


def _cli_count(value: object, option: str) -> int | None:
    """Return a CLI integer, or None when the option was omitted.

    Args:
        value: Raw CLI value.
        option: Option name used in the error.

    Returns:
        The CLI integer, or None when unset.
    """
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        _exit_not_integer(option)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            _exit_not_integer(option)
    _exit_not_integer(option)


def resolve_matrix_limits(
    file_jobs: object,
    file_parallel: object,
    cli_jobs: object,
    cli_parallel: object,
) -> tuple[int, int | None]:
    """Resolve job count and max parallel from config, then CLI.

    A config value of ``0`` for max parallel means the key is omitted. An
    explicit CLI value is kept, including values that later fail validation.

    Args:
        file_jobs: ``matrix_jobs`` from TOML or INI.
        file_parallel: ``matrix_max_parallel`` from TOML or INI.
        cli_jobs: ``--matrix-jobs``, or None when omitted.
        cli_parallel: ``--matrix-max-parallel``, or None when omitted.

    Returns:
        Job count and optional max parallel.
    """
    jobs_option = _cli_count(cli_jobs, "--matrix-jobs")
    parallel_option = _cli_count(cli_parallel, "--matrix-max-parallel")
    jobs = _coerce_count(file_jobs) if jobs_option is None else jobs_option
    if parallel_option is None:
        parsed_parallel = _coerce_count(file_parallel)
        parallel = parsed_parallel if parsed_parallel > 0 else None
    else:
        parallel = parallel_option
    return jobs, parallel


def require_matrix_limits(
    matrix_jobs: int,
    matrix_max_parallel: int | None,
) -> tuple[int, int | None]:
    """Validate limits used to build or run a scenario matrix.

    Args:
        matrix_jobs: Configured job count.
        matrix_max_parallel: Configured cap, or None when omitted.

    Returns:
        The same values when they are valid.
    """
    if matrix_jobs < 1:
        logger.critical(
            "matrix_jobs must be a positive integer; set matrix_jobs or pass --matrix-jobs",
        )
        sys.exit(1)
    if matrix_max_parallel is not None and matrix_max_parallel < 1:
        logger.critical(
            "matrix_max_parallel must be a positive integer, got %s",
            matrix_max_parallel,
        )
        sys.exit(1)
    return matrix_jobs, matrix_max_parallel


def write_job_matrix(matrix: JobMatrix) -> None:
    """Print the matrix or append it to ``GITHUB_OUTPUT``.

    Args:
        matrix: Matrix to publish.
    """
    payload = matrix.as_dict()
    gh_output = os.getenv("GITHUB_OUTPUT")
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    if not gh_output and not in_actions:
        print(json.dumps(payload, indent=2))  # noqa: T201
        return
    if not gh_output:
        logger.critical("GITHUB_OUTPUT environment variable not set")
        sys.exit(1)

    lines: list[str] = []
    for key in ("jobs", "scenarios", "max_parallel"):
        if key not in payload:
            continue
        value = json.dumps(payload[key])
        if "\n" in value:
            eof = f"EOF-{uuid.uuid4()}"
            lines.append(f"{key}<<{eof}\n{value}\n{eof}\n")
        else:
            lines.append(f"{key}={value}\n")
    with Path(gh_output).open("a", encoding="utf-8") as handle:
        handle.write("".join(lines))


def write_scenario_matrix(
    project_dir: Path,
    impact_file: str | None,
    matrix_jobs: int,
    matrix_max_parallel: int | None,
    collection: Collection,
) -> None:
    """Load an impact report and publish its scenario job matrix.

    Args:
        project_dir: Collection root.
        impact_file: Impact-report path.
        matrix_jobs: Configured job count.
        matrix_max_parallel: Configured cap, or None when omitted.
        collection: Collection used to validate the report.
    """
    if not impact_file:
        logger.critical("--gh-matrix-jobs requires an impact file")
        sys.exit(1)
    job_count, max_parallel = require_matrix_limits(matrix_jobs, matrix_max_parallel)
    report = load_impact_report(impact_file, project_dir, collection=collection)
    if report is None:  # pragma: no cover
        logger.critical("--gh-matrix-jobs requires an impact file")
        sys.exit(1)
    write_job_matrix(build_job_matrix(report, project_dir, job_count, max_parallel))


def assign_job(
    report: ImpactReport,
    project_dir: Path,
    matrix_jobs: int,
    matrix_max_parallel: int | None,
    job_id: str,
) -> ImpactReport:
    """Return the impact report narrowed to one matrix job.

    Args:
        report: Full impact report.
        project_dir: Collection root.
        matrix_jobs: Configured job count.
        matrix_max_parallel: Configured cap, or None when omitted.
        job_id: Job id selected with ``--matrix-job``.

    Returns:
        Report containing only that job's scenarios.
    """
    job_count, max_parallel = require_matrix_limits(matrix_jobs, matrix_max_parallel)
    require_integration_targets(report, project_dir)
    matrix = build_job_matrix(report, project_dir, job_count, max_parallel)
    try:
        names = job_scenario_names(matrix, job_id)
    except ValueError as exc:
        logger.critical("%s", exc)
        sys.exit(1)
    return narrow_impact_report(report, job_id, names)


def apply_matrix_job(
    report: ImpactReport | None,
    project_dir: Path,
    matrix_jobs: int,
    matrix_max_parallel: int | None,
    job_id: str | None,
) -> ImpactReport | None:
    """Narrow a report to one job, or return it unchanged.

    Args:
        report: Loaded impact report, if any.
        project_dir: Collection root.
        matrix_jobs: Configured job count.
        matrix_max_parallel: Configured cap, or None when omitted.
        job_id: Job id from ``--matrix-job``, or None when that option is omitted.

    Returns:
        The original report, or the report narrowed to ``job_id``.
    """
    if not job_id:
        return report
    if report is None:
        logger.critical("--matrix-job requires an impact file")
        sys.exit(1)
    return assign_job(report, project_dir, matrix_jobs, matrix_max_parallel, job_id)
