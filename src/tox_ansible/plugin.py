# cspell:ignore envlist
"""tox plugin to emit a github matrix."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import uuid

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

import yaml

from tox.config.loader.memory import MemoryLoader
from tox.config.loader.section import Section
from tox.config.loader.str_convert import StrConvert
from tox.config.sets import ConfigSet, CoreConfigSet, EnvConfigSet
from tox.plugin import impl
from tox.tox_env.python.api import PY_FACTORS_RE


if TYPE_CHECKING:
    from tox.config.cli.parser import ToxParser
    from tox.config.types import EnvList
    from tox.session.state import State

logger = logging.getLogger(__name__)

ALLOWED_EXTERNALS = [
    "ade",
    "bash",
    "echo",
    "git",
    "sh",
]
ENV_LIST = """
galaxy
{integration, sanity, unit}-py3.10-{2.16, 2.17}
{integration, sanity, unit}-py3.11-{2.17, 2.18, 2.19}
{integration, sanity, unit}-py3.12-{2.17, 2.18, 2.19, 2.20, milestone, devel}
{integration, sanity, unit}-py3.13-{2.18, 2.19, 2.20, milestone, devel}
{integration, sanity, unit}-py3.14-{2.20, 2.20, milestone, devel}
"""
# ^ py314 is NOT supported before 2.20! If is in official metadata of the
# release branch, is not supported.
# https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix

# Without the minimal pytest-ansible condition, installation may fail in some
# cases (pip, uv).
OUR_DEPS = [
    "pytest>=7.4.3",  # Oct 2023
    "pytest-xdist>=3.4.0",  # Nov 2023
    "pytest-ansible>=v4.1.1",  # latest version still supporting py39 (Oct 2023)
    "ansible-compat>=25.11.0",  # Nov 2025
]

T = TypeVar("T", bound=ConfigSet)


class AnsibleConfigSet(ConfigSet):
    """The ansible configuration."""

    def register_config(self) -> None:
        """Register the ansible configuration."""
        self.add_config(
            "skip",
            of_type=list[str],
            default=[],
            desc="ansible configuration",
        )


@dataclass
class AnsibleTestConf:  # pylint: disable=too-many-instance-attributes
    """Ansible test configuration.

    Attributes:
        description: The description of the test.
        deps: The dependencies for the test.
        setenv: The set environment variables for the test.
        skip_install: Skip the installation.
        allowlist_externals: The allowed external commands.
        commands_pre: The pre-run commands.
        commands: The commands to run.
        passenv: The pass environment
    """

    description: str
    deps: str
    setenv: str
    skip_install: bool
    allowlist_externals: list[str] = field(default_factory=list)
    commands_pre: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    passenv: list[str] = field(default_factory=list)


def custom_sort(string: str) -> tuple[int, ...]:
    """Convert a env name into a tuple of ints.

    In the case of a string, use the ord() of the first two characters.

    Args:
        string: The string to sort.

    Returns:
        The tuple of converted values.
    """
    parts = re.split(r"\.|-|py", string)
    converted = []
    for part in parts:
        if not part:
            continue
        try:
            converted.append(int(part))
        except ValueError:
            num_part = "".join((str(ord(char)).rjust(3, "0")) for char in part[0:2])
            converted.append(int(num_part))
    return tuple(converted)


@impl
def tox_add_option(parser: ToxParser) -> None:
    """Add the --gh-matrix option to the tox CLI.

    Args:
        parser: The tox CLI parser.
    """
    parser.add_argument(
        "--matrix-scope",
        default="all",
        choices=["all", "galaxy", "sanity", "integration", "unit"],
        help="Emit a github matrix specific to scope mentioned",
    )

    parser.add_argument(
        "--gh-matrix",
        action="store_true",
        default=False,
        help="Emit a github matrix",
    )

    parser.add_argument(
        "--ansible",
        action="store_true",
        default=False,
        help="Enable ansible testing",
    )


@impl
def tox_add_core_config(
    core_conf: CoreConfigSet,  # noqa: ARG001 # pylint: disable=unused-argument
    state: State,
) -> None:
    """Dump the environment list and exit.

    Args:
        core_conf: The core configuration object.
        state: The state object.
    """
    if state.conf.options.gh_matrix and not state.conf.options.ansible:
        err = "The --gh-matrix option requires --ansible"
        logger.critical(err)
        sys.exit(1)

    if not state.conf.options.ansible:
        return

    if state.conf.src_path.name == "tox.ini":
        msg = (
            "Using a default tox.ini file with tox-ansible plugin is not recommended."
            " Consider using a tox-ansible.ini file and specify it on the command line"
            " (`tox --ansible -c tox-ansible.ini`) to avoid unintentionally overriding"
            " the tox-ansible environment configurations."
        )
        logger.warning(msg)

    env_list = add_ansible_matrix(state)

    if not state.conf.options.gh_matrix:
        return

    generate_gh_matrix(env_list=env_list, section=state.conf.options.matrix_scope)
    sys.exit(0)


@impl
def tox_add_env_config(env_conf: EnvConfigSet, state: State) -> None:
    """Add the test requirements and ansible-core to the virtual environment.

    Args:
        env_conf: The environment configuration object.
        state: The state object.
    """
    if not state.conf.options.ansible:
        return

    factors = env_conf.name.split("-")
    expected_factors = 3
    if "galaxy" not in factors and (
        len(factors) != expected_factors
        or factors[0]
        not in [
            "integration",
            "sanity",
            "unit",
        ]
    ):
        return
    # When run nested, work_dir might become .tox instead of cwd and we don't
    # want to use `state.conf.work_dir` to find the galaxy file. PWD is more
    # reliable, even if there is a chance it might be also changed.
    galaxy_path = state.conf.src_path.parent.resolve() / "galaxy.yml"
    collection = get_collection(galaxy_path=galaxy_path)
    pos_args = state.conf.pos_args(to_path=None)

    test_type = factors[0]
    ansible_version = factors[-1] if len(factors) == expected_factors else ""

    conf = AnsibleTestConf(
        allowlist_externals=ALLOWED_EXTERNALS,
        commands_pre=conf_commands_pre(
            collection=collection,
            env_conf=env_conf,
            test_type=test_type,
            ansible_version=ansible_version,
        ),
        commands=conf_commands(
            collection=collection,
            env_conf=env_conf,
            pos_args=pos_args,
            test_type=test_type,
        ),
        description=desc_for_env(env_conf.name),
        deps=conf_deps(env_conf=env_conf, test_type=test_type),
        passenv=conf_passenv(),
        setenv=conf_setenv(env_conf=env_conf, test_type=test_type),
        skip_install=True,
    )
    loader = MemoryLoader(**asdict(conf))
    env_conf.loaders.append(loader)


def desc_for_env(env: str) -> str:
    """Generate a description for an environment.

    Args:
        env: The environment name.

    Returns:
        The environment description.
    """
    if env == "galaxy":
        return "Build collection and run galaxy-importer on it"
    test_type, python, core = env.split("-")
    ansible_pkg = "ansible-core"

    return f"{test_type.capitalize()} tests using {ansible_pkg} {core} and python {python[2:]}"


def in_action() -> bool:
    """Check if running on Github Actions platform.

    Returns:
        True if running on Github Actions platform.
    """
    return os.environ.get("GITHUB_ACTIONS") == "true"


def add_ansible_matrix(state: State) -> EnvList:
    """Add the ansible matrix to the state.

    Args:
        state: The state object.

    Returns:
        The environment list.
    """
    ansible_config = state.conf.get_section_config(
        Section(None, "ansible"),
        base=[],
        of_type=AnsibleConfigSet,
        for_env=None,
    )
    env_list = StrConvert().to_env_list(ENV_LIST)
    env_list.envs = [
        env for env in env_list.envs if all(skip not in env for skip in ansible_config["skip"])
    ]
    env_list.envs = sorted(env_list.envs, key=custom_sort)
    state.conf.core.loaders.append(
        MemoryLoader(env_list=env_list),
    )
    return env_list


def _check_num_candidates(candidates: list[str], env_name: str) -> None:
    """Check the number of candidates.

    Args:
        candidates: The candidates.
        env_name: The environment name.
    """
    if env_name == "galaxy":
        return
    if len(candidates) > 1:
        err = f"Multiple python versions found in {env_name}"
        logger.critical(err)
        sys.exit(1)
    if len(candidates) == 0:
        err = f"No python version found in {env_name}"
        logger.critical(err)
        sys.exit(1)


def _gen_version(candidates: list[str]) -> str:
    """Generate the version from the candidates.

    Args:
        candidates: The candidates.

    Returns:
        The version.
    """
    if "." in candidates[0]:
        return candidates[0]
    return f"{candidates[0][0]}.{candidates[0][1:]}"


def generate_gh_matrix(env_list: EnvList, section: str) -> None:
    """Generate the github matrix.

    Args:
        env_list: The environment list.
        section: The test section to be generated.
    """
    results = []
    for env_name in env_list.envs:
        if section != "all" and not env_name.startswith(section):
            continue
        candidates = []
        factors = env_name.split("-")
        for factor in factors:
            match = PY_FACTORS_RE.match(factor)
            if match:
                candidates.append(match[2])
        if env_name == "galaxy":
            candidates = ["3.14"]

        _check_num_candidates(candidates=candidates, env_name=env_name)
        version = _gen_version(candidates=candidates)

        results.append(
            {
                "description": desc_for_env(env_name),
                "factors": factors,
                "name": env_name,
                "python": version,
            },
        )

    gh_output = os.getenv("GITHUB_OUTPUT")
    if not gh_output and not in_action():
        value = json.dumps(results, indent=2, sort_keys=True)
        print(value)  # noqa: T201
        return

    if not gh_output:
        err = "GITHUB_OUTPUT environment variable not set"
        logger.critical(err)
        sys.exit(1)

    value = json.dumps(results)

    if "\n" in value:
        eof = f"EOF-{uuid.uuid4()}"
        encoded = f"envlist<<{eof}\n{value}\n{eof}\n"
    else:
        encoded = f"envlist={value}\n"

    with Path(gh_output).open("a", encoding="utf-8") as fileh:
        fileh.write(encoded)


@dataclass
class Collection:
    """Collection information.

    Attributes:
        name: The collection name.
        namespace: The collection namespace.
        version: The collection version.
    """

    name: str
    namespace: str
    version: str


def get_collection(galaxy_path: Path) -> Collection:
    """Extract collection information from the galaxy.yml file.

    Args:
        galaxy_path: The path to the galaxy.yml file.

    Returns:
        The collection name and namespace.
    """
    try:
        with galaxy_path.open() as galaxy_file:
            galaxy = yaml.safe_load(galaxy_file)
    except FileNotFoundError:
        err = f"Unable to find galaxy.yml file at {galaxy_path}"
        logger.critical(err)
        sys.exit(1)

    try:
        c_name = galaxy["name"]
        c_namespace = galaxy["namespace"]
        c_version = galaxy["version"]
    except KeyError as exc:
        err = f"Unable to find {exc} in galaxy.yml"
        logger.critical(err)
        sys.exit(1)
    return Collection(name=c_name, namespace=c_namespace, version=c_version)


def conf_commands(
    collection: Collection,
    env_conf: EnvConfigSet,
    pos_args: tuple[str, ...] | None,
    test_type: str,
) -> list[str]:
    """Build the commands for the tox environment.

    Args:
        collection: The collection info.
        env_conf: The tox environment configuration object.
        pos_args: Positional arguments passed to tox command.
        test_type: The test type, either "integration", "unit", or "sanity".

    Returns:
        The commands to run.
    """
    if test_type in ["integration", "unit"]:
        return conf_commands_for_integration_unit(
            pos_args=pos_args,
            test_type=test_type,
        )
    if test_type == "sanity":
        return conf_commands_for_sanity(
            collection=collection,
            env_conf=env_conf,
            pos_args=pos_args,
        )
    if test_type == "galaxy":
        return conf_commands_for_galaxy(
            collection=collection,
            env_conf=env_conf,
            pos_args=pos_args,
        )
    err = f"Unknown test type {test_type}"
    logger.critical(err)
    sys.exit(1)


def conf_commands_for_integration_unit(
    pos_args: tuple[str, ...] | None,
    test_type: str,
) -> list[str]:
    """Build the commands for integration and unit tests.

    Args:
        pos_args: Positional arguments passed to tox command.
        test_type: The test type, either "integration" or "unit".

    Returns:
        The commands to run.
    """
    args = f" {' '.join(pos_args)} " if pos_args else " "

    # Use pytest ansible unit inject only to inject the collection path
    # into the collection finder
    command = f"python3 -m pytest --ansible-unit-inject-only{args}{Path()}/tests/{test_type}"
    return [command]


def conf_commands_for_sanity(
    collection: Collection,
    env_conf: EnvConfigSet,
    pos_args: tuple[str, ...] | None,
) -> list[str]:
    """Add commands for sanity tests.

    Args:
        collection: The collection info.
        env_conf: The tox environment configuration object.
        pos_args: Positional arguments passed to tox command.

    Returns:
        The commands to run.
    """
    commands = []

    args = f" {' '.join(pos_args)}" if pos_args else ""

    py_ver = env_conf.name.split("-")[1].replace("py", "")

    command = f"ansible-test sanity --local --requirements --python {py_ver}{args}"
    ch_dir = (
        f"cd {{envsitepackagesdir}}/ansible_collections/{collection.namespace}/{collection.name}"
    )
    full_command = f"bash -c '{ch_dir} && {command}'"
    commands.append(full_command)
    return commands


def conf_commands_for_galaxy(
    collection: Collection,  # noqa: ARG001
    env_conf: EnvConfigSet,
    pos_args: tuple[str, ...] | None,  # noqa: ARG001
) -> list[str]:
    """Add commands for sanity tests.

    Args:
        collection: The collection info.
        env_conf: The tox environment configuration object.
        pos_args: Positional arguments passed to tox command.

    Returns:
        The commands to run.
    """
    commands = []
    env_tmp_dir = env_conf["env_tmp_dir"]
    env_log_dir = env_conf["env_log_dir"]
    env_python = env_conf["env_python"]
    config_dir = env_conf._conf.src_path.parent.resolve()
    commands.append(
        f"bash -c 'cd {env_log_dir} && "
        f"{env_python} -m galaxy_importer.main "
        f"--git-clone-path {config_dir} --output-path {env_tmp_dir}'"
    )

    return commands


def conf_commands_pre(
    env_conf: EnvConfigSet,
    collection: Collection,
    test_type: str,
    ansible_version: str,
) -> list[str]:
    """Install the collection using ade (ansible-dev-environment).

    Args:
        env_conf: The tox environment configuration object.
        collection: The collection info.
        test_type: The test type, either "integration", "unit", "sanity", or "galaxy".
        ansible_version: The ansible version factor from the env name.

    Returns:
        The commands to pre run.
    """
    if test_type == "galaxy":
        return []

    commands = []
    envdir = env_conf["env_dir"]
    end_group = "echo ::endgroup::"

    if ansible_version in ("devel", "milestone"):
        acv = ansible_version
    else:
        acv = f"stable-{ansible_version}"

    if in_action():
        commands.append("echo ::group::Install collection with ade")
    ade_cmd = f"ade install -e --venv {envdir} --acv {acv} --no-seed --im none ."
    commands.append(
        f"bash -c '{ade_cmd}; rc=$?; if [ $rc -ne 0 ] && [ $rc -ne 2 ]; then exit $rc; fi'",
    )
    if in_action():
        commands.append(end_group)

    if test_type == "sanity":
        collection_path = (
            f"{{envsitepackagesdir}}/ansible_collections/{collection.namespace}/{collection.name}"
        )
        if in_action():
            commands.append("echo ::group::Initialize the collection to avoid ansible #68499")
        git_cfg = "git config --global init.defaultBranch main"
        git_init = "git init ."
        commands.append(f"bash -c 'cd {collection_path} && {git_cfg} && {git_init}'")
        if in_action():
            commands.append(end_group)

    return commands


def conf_deps(env_conf: EnvConfigSet, test_type: str) -> str:  # noqa: ARG001
    """Add dependencies to the tox environment.

    Args:
        env_conf: The tox environment configuration object.
        test_type: The test type, either "integration", "unit", or "sanity".

    Returns:
        The dependencies.
    """
    deps = []
    cwd = Path.cwd()
    if test_type == "galaxy":
        deps.append("galaxy-importer>=0.4.31")
    else:
        deps.append("ansible-dev-environment>=26.2.0")
        if test_type in ("integration", "unit"):
            deps.extend(OUR_DEPS)
            try:
                with (cwd / "test-requirements.txt").open() as fileh:
                    deps.extend(fileh.read().splitlines())
            except FileNotFoundError:
                pass
            try:
                with (cwd / "requirements-test.txt").open() as fileh:
                    deps.extend(fileh.read().splitlines())
            except FileNotFoundError:
                pass
            try:
                with (cwd / "requirements.txt").open() as fileh:
                    deps.extend(fileh.read().splitlines())
            except FileNotFoundError:
                pass

    return "\n".join(deps)


def conf_passenv() -> list[str]:
    """Build the pass environment variables for the tox environment.

    Returns:
        The pass environment variables.
    """
    passenv = []
    passenv.append("GITHUB_TOKEN")
    return passenv


def conf_setenv(env_conf: EnvConfigSet, test_type: str) -> str:
    """Build the set environment variables for the tox environment.

    Set the XDG_CACHE_HOME to the environment directory to isolate it

    Args:
        env_conf: The tox environment configuration object.
        test_type: The test type.

    Returns:
        The set environment variables.
    """
    setenv = [
        f"XDG_CACHE_HOME={env_conf['env_dir']}/.cache",
    ]

    if test_type != "galaxy":
        setenv.insert(0, "ANSIBLE_COLLECTIONS_PATH=.")

    # due to the ceilings used by galaxy-importer, use of constraints will
    # likely cause installation failures.
    if test_type == "galaxy":
        setenv.append("PIP_CONSTRAINT=/dev/null")
        setenv.append("UV_CONSTRAINT=/dev/null")
    return "\n".join(setenv)
