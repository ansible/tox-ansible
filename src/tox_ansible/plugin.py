# cspell:ignore envlist
"""tox plugin to emit a github matrix."""

import json
import logging
import os
import re
import sys
import uuid

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Tuple, TypeVar

import yaml

from tox.config.cli.parser import ToxParser
from tox.config.loader.memory import MemoryLoader
from tox.config.loader.section import Section
from tox.config.loader.str_convert import StrConvert
from tox.config.sets import ConfigSet, CoreConfigSet, EnvConfigSet
from tox.config.types import EnvList
from tox.plugin import impl
from tox.session.state import State
from tox.tox_env.python.api import PY_FACTORS_RE


ALLOWED_EXTERNALS = [
    "bash",
    "cp",
    "git",
    "rm",
    "rsync",
    "mkdir",
    "cd",
    "echo",
]
ENV_LIST = """
{integration, sanity, unit}-py3.8-{2.9, 2.12, 2.13}
{integration, sanity, unit}-py3.9-{2.12, 2.13, 2.14, milestone, devel}
{integration, sanity, unit}-py3.10-{2.12, 2.13, 2.14, milestone, devel}
{integration, sanity, unit}-py3.11-{2.14, milestone, devel}
"""
TOX_WORK_DIR = Path()
OUR_DEPS = [
    "pytest",
    "pytest-xdist",
    "git+https://github.com/ansible-community/pytest-ansible.git",
]

T = TypeVar("T", bound=ConfigSet)


class AnsibleConfigSet(ConfigSet):
    """The ansible configuration."""

    def register_config(self: T) -> None:
        """Register the ansible configuration."""
        self.add_config(
            "skip",
            of_type=List[str],
            default=[],
            desc="ansible configuration",
        )


@dataclass
class AnsibleTestConf:  # pylint: disable=too-many-instance-attributes
    """Ansible test configuration."""

    description: str
    deps: str
    setenv: str
    skip_install: bool
    allowlist_externals: List[str] = field(default_factory=list)
    commands_pre: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    passenv: List[str] = field(default_factory=list)


def custom_sort(string: str) -> Tuple[int, ...]:
    """Convert a env name into a tuple of ints.

    In the case of a string, use the ord() of the first two characters.

    :param string: The string to sort.
    :return: The tuple of converted values.
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

    :param parser: The tox CLI parser.
    """
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
    core_conf: CoreConfigSet,  # pylint: disable=unused-argument
    state: State,
) -> None:
    """Dump the environment list and exit.

    :param core_conf: The core configuration object.
    :param state: The state object.
    """
    if state.conf.options.gh_matrix and not state.conf.options.ansible:
        err = "The --gh-matrix option requires --ansible"
        logging.critical(err)
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
        logging.warning(msg)

    global TOX_WORK_DIR  # pylint: disable=global-statement # noqa: PLW0603
    TOX_WORK_DIR = state.conf.work_dir
    env_list = add_ansible_matrix(state)

    if not state.conf.options.gh_matrix:
        return

    generate_gh_matrix(env_list=env_list)
    sys.exit(0)


@impl
def tox_add_env_config(env_conf: EnvConfigSet, state: State) -> None:
    """Add the test requirements and ansible-core to the virtual environment.

    :param env_conf: The environment configuration object.
    :param state: The state object.
    """
    if not state.conf.options.ansible:
        return

    factors = env_conf.name.split("-")
    expected_factors = 3
    if len(factors) != expected_factors or factors[0] not in [
        "integration",
        "sanity",
        "unit",
    ]:
        return

    galaxy_path = TOX_WORK_DIR / "galaxy.yml"
    c_name, c_namespace = get_collection_name(galaxy_path=galaxy_path)

    conf = AnsibleTestConf(
        allowlist_externals=ALLOWED_EXTERNALS,
        commands_pre=conf_commands_pre(
            c_name=c_name,
            c_namespace=c_namespace,
            env_conf=env_conf,
        ),
        commands=conf_commands(
            c_name=c_name,
            c_namespace=c_namespace,
            env_conf=env_conf,
            test_type=factors[0],
        ),
        description=desc_for_env(env_conf.name),
        deps=conf_deps(env_conf=env_conf, test_type=factors[0]),
        passenv=conf_passenv(),
        setenv=conf_setenv(env_conf),
        skip_install=True,
    )
    loader = MemoryLoader(**asdict(conf))
    env_conf.loaders.append(loader)


def desc_for_env(env: str) -> str:
    """Generate a description for an environment.

    :param env: The environment name.
    :return: The environment description.
    """
    test_type, python, core = env.split("-")
    ansible_pkg = "ansible" if core == "2.9" else "ansible-core"

    description = (
        f"{test_type.capitalize()} tests using {ansible_pkg} {core} and python {python[2:]}"
    )
    return description


def in_action() -> bool:
    """Check if running on Github Actions platform.

    :return: True if running on Github Actions platform
    """
    return os.environ.get("GITHUB_ACTIONS") == "true"


def add_ansible_matrix(state: State) -> EnvList:
    """Add the ansible matrix to the state.

    :param state: The state object.
    :return: The environment list.
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


def generate_gh_matrix(env_list: EnvList) -> None:
    """Generate the github matrix.

    :param env_list: The environment list.
    """
    results = []

    for env_name in env_list.envs:
        candidates = []
        factors = env_name.split("-")
        for factor in factors:
            match = PY_FACTORS_RE.match(factor)
            if match:
                candidates.append(match[2])
        if len(candidates) > 1:
            err = f"Multiple python versions found in {env_name}"
            logging.critical(err)
            sys.exit(1)
        if len(candidates) == 0:
            err = f"No python versions found in {env_name}"
            logging.critical(err)
            sys.exit(1)
        if "." in candidates[0]:
            version = candidates[0]
        else:
            version = f"{candidates[0][0]}.{candidates[0][1:]}"
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
        logging.critical(err)
        sys.exit(1)

    value = json.dumps(results)

    if "\n" in value:
        eof = f"EOF-{uuid.uuid4()}"
        encoded = f"envlist<<{eof}\n{value}\n{eof}\n"
    else:
        encoded = f"envlist={value}\n"

    with Path(gh_output).open("a", encoding="utf-8") as fileh:
        fileh.write(encoded)


def get_collection_name(galaxy_path: Path) -> Tuple[str, str]:
    """Extract collection information from the galaxy.yml file.

    :param galaxy_path: The path to the galaxy.yml file.
    :return: The collection name.
    """
    try:
        with galaxy_path.open() as galaxy_file:
            galaxy = yaml.safe_load(galaxy_file)
    except FileNotFoundError:
        err = f"Unable to find galaxy.yml file at {galaxy_path}"
        logging.critical(err)
        sys.exit(1)

    try:
        c_name = galaxy["name"]
        c_namespace = galaxy["namespace"]
    except KeyError as exc:
        err = f"Unable to find {exc} in galaxy.yml"
        logging.critical(err)
        sys.exit(1)
    return c_name, c_namespace


def conf_commands(
    c_name: str,
    c_namespace: str,
    env_conf: EnvConfigSet,
    test_type: str,
) -> List[str]:
    """Build the commands for the tox environment.

    :param c_name: The collection name.
    :param c_namespace: The collection namespace.
    :param test_type: The test type, either "integration", "unit", or "sanity".
    :param env_conf: The tox environment configuration object.
    :return: The commands to run.
    """
    if test_type in ["integration", "unit"]:
        return conf_commands_for_integration_unit(
            env_conf=env_conf,
            test_type=test_type,
        )
    if test_type == "sanity":
        return conf_commands_for_sanity(
            c_name=c_name,
            c_namespace=c_namespace,
            env_conf=env_conf,
        )
    err = f"Unknown test type {test_type}"
    logging.critical(err)
    sys.exit(1)


def conf_commands_for_integration_unit(
    env_conf: EnvConfigSet,
    test_type: str,
) -> List[str]:
    """Build the commands for integration and unit tests.

    :param env_conf: The tox environment configuration object.
    :param test_type: The test type, either "integration" or "unit".
    :return: The command to run.
    """
    commands = []
    envtmpdir = env_conf["envtmpdir"]
    # Use pytest ansible unit inject only to inject the collection path
    # into the collection finder
    command = f"python -m pytest --ansible-unit-inject-only {TOX_WORK_DIR}/tests/{test_type}"
    unit_ch_dir = f"{envtmpdir}/collections/"
    if test_type == "unit":
        commands.append(f"bash -c 'cd {unit_ch_dir} && {command}'")
    else:
        commands.append(command)
    return commands


def conf_commands_for_sanity(
    c_name: str,
    c_namespace: str,
    env_conf: EnvConfigSet,
) -> List[str]:
    """Add commands for sanity tests.

    :param c_name: The collection name.
    :param c_namespace: The collection namespace.
    :param env_conf: The tox environment configuration object.
    :return: The commands to run.
    """
    commands = []
    envtmpdir = env_conf["envtmpdir"]

    py_ver = env_conf["basepython"][0].replace("py", "")
    if "." not in py_ver:
        py_ver = f"{py_ver[0]}.{py_ver[1:]}"

    command = f"ansible-test sanity --local --requirements --python {py_ver}"
    ch_dir = f"cd {envtmpdir}/collections/ansible_collections/{c_namespace}/{c_name}"
    full_command = f"bash -c '{ch_dir} && {command}'"
    commands.append(full_command)
    return commands


def conf_commands_pre(
    env_conf: EnvConfigSet,
    c_name: str,
    c_namespace: str,
) -> List[str]:
    """Build and install the collection.

    :param env_conf: The tox environment configuration object.
    :param c_name: The collection name.
    :param c_namespace: The collection namespace.
    :return: The commands to pre run.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    commands = []

    # Define some directories"
    envtmpdir = env_conf["envtmpdir"]
    collections_root = f"{envtmpdir}/collections"
    collection_installed_at = f"{collections_root}/ansible_collections/{c_namespace}/{c_name}"
    galaxy_build_dir = f"{envtmpdir}/collection_build"
    end_group = "echo ::endgroup::"

    if in_action():
        group = "echo ::group::Make the galaxy build dir"
        commands.append(group)
    commands.append(f"mkdir {galaxy_build_dir}")
    if in_action():
        commands.append(end_group)

    if in_action():
        group = "echo ::group::Copy the collection to the galaxy build dir"
        commands.append(group)
    cd_tox_dir = f"cd {TOX_WORK_DIR}"
    rsync_cmd = f'rsync -r --cvs-exclude --filter=":- .gitignore" . {galaxy_build_dir}'
    full_cmd = f"bash -c '{cd_tox_dir} && {rsync_cmd}'"
    commands.append(full_cmd)
    if in_action():
        commands.append(end_group)

    if in_action():
        group = "echo ::group::Build and install the collection"
        commands.append(group)
    cd_build_dir = f"cd {galaxy_build_dir}"
    build_cmd = "ansible-galaxy collection build"
    tar_file = f"{c_namespace}-{c_name}-*.tar.gz"
    install_cmd = f"ansible-galaxy collection install {tar_file} -p {collections_root}"
    full_cmd = f"bash -c '{cd_build_dir} && {build_cmd} && {install_cmd}'"
    commands.append(full_cmd)
    if in_action():
        commands.append(end_group)

    if in_action():
        group = "echo ::group::Initialize the collection to avoid ansible #68499"
        commands.append(group)
    cd_install_dir = f"cd {collection_installed_at}"
    git_cfg = "git config --global init.defaultBranch main"
    git_init = "git init ."
    full_cmd = f"bash -c '{cd_install_dir} && {git_cfg} && {git_init}'"
    commands.append(full_cmd)
    if in_action():
        commands.append(end_group)

    if env_conf.name == "sanity-py3.8-2.9":
        # Avoid "Setuptools is replacing distutils"
        if in_action():
            group = "echo ::group::Use old setuptools for sanity-py3.8-2.9"
            commands.append(group)
        pip_install = "pip install setuptools==57.5.0"
        commands.append(pip_install)
        if in_action():
            commands.append(end_group)

    return commands


def conf_deps(env_conf: EnvConfigSet, test_type: str) -> str:
    """Add dependencies to the tox environment.

    :param env_conf: The environment configuration.
    :param test_type: The test type.
    :return: The dependencies.
    """
    deps = []
    if test_type in ["integration", "unit"]:
        deps.extend(OUR_DEPS)
        try:
            with (TOX_WORK_DIR / "test-requirements.txt").open() as fileh:
                deps.extend(fileh.read().splitlines())
        except FileNotFoundError:
            pass
        try:
            with (TOX_WORK_DIR / "requirements.txt").open() as fileh:
                deps.extend(fileh.read().splitlines())
        except FileNotFoundError:
            pass

    ansible_version = env_conf.name.split("-")[2]
    base_url = "https://github.com/ansible/ansible/archive/"
    if ansible_version in ["devel", "milestone"]:
        ansible_package = f"{base_url}{ansible_version}.tar.gz"
    else:
        ansible_package = f"{base_url}stable-{ansible_version}.tar.gz"
    deps.append(ansible_package)
    return "\n".join(deps)


def conf_passenv() -> List[str]:
    """Build the pass environment variables for the tox environment.

    :return: The pass environment variables.
    """
    passenv = []
    passenv.append("GITHUB_TOKEN")
    return passenv


def conf_setenv(env_conf: EnvConfigSet) -> str:
    """Build the set environment variables for the tox environment.

    :param env_conf: The environment configuration.
    :return: The set environment variables.
    """
    envtmpdir = env_conf["envtmpdir"]
    setenv = []
    setenv.append(f"ANSIBLE_COLLECTIONS_PATHS={envtmpdir}/collections/")
    return "\n".join(setenv)
