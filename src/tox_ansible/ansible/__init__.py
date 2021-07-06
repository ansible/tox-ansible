import copy
import glob
import logging
import sys
from os import path
from typing import Any, Dict

from tox_ansible._yaml import load_yaml
from tox_ansible.tox_helper import Tox

from ..tox_ansible_test_case import ToxAnsibleTestCase
from ..tox_lint_case import ToxLintCase
from ..tox_molecule_case import ToxMoleculeCase
from .scenario import Scenario

LOCAL_CONFIG_FILE = ".config/molecule/config.yml"


class Ansible(object):
    """A generalized class that handles interactions between the plugin and
    Ansible structures. It will determine if we are in an Ansible folder
    structure, what kind, and fetch the relevant information back from the
    filesystem for the caller."""

    def __init__(self, base="", options=None):
        """Create an Ansible object to introspect on whether the given
        directory is an Ansible structure or not. Currently aware of a
        collection and a role.

        :param base: Path to the folder. Defaults to being relative to
        os.path.curdir, but can be absolute"""
        if path.isabs(base):
            self.directory = base
        else:
            self.directory = path.abspath(path.join(path.curdir, base))
        self._scenarios = None
        self.options = options
        self.tox = Tox()

    def molecule_config_files(self):
        """Determine if there is a global molecule configuration file at the
        project level. If there are molecule base configuration file(s) passed
        as an option in the tox.ini file, those will take precedence over the
        global configuration file at the project level.

        :return: A list of absolute path of molecule base configuration file.
                 None, otherwise."""
        global_molecule_config = path.join(self.directory, LOCAL_CONFIG_FILE)

        if self.options.molecule_config_files:
            return self.options.molecule_config_files

        if path.isfile(global_molecule_config):
            return [global_molecule_config]

        return None

    @property
    def is_ansible(self):
        """Determine if the specified directory is an Ansible structure or not

        :return: True if this is an Ansible structure. False, otherwise."""
        return len(self.scenarios) > 0 or path.isfile(
            path.join(self.directory, "galaxy.yml")
        )

    @property
    def molecule_config(self):
        """Reads all the molecule base configuration files present and adds them
        in the self.molecule_config field.

        :return: A list of one or multiple dictionaries including the content of
                 the molecule base configuration file(s)
        """
        configs = []
        config_files_list = self.molecule_config_files()
        if config_files_list:
            for config_file in config_files_list:
                configs.append(load_yaml(config_file))

        return configs

    @property
    def scenarios(self):
        """Recursively searches the potential Ansible directory and looks for any
        scenario directories found.

        :return: An array of Scenario objects, empty if none are found"""
        # Don't walk the filesystem more often than necessary
        if self._scenarios is not None:
            return self._scenarios
        self._scenarios = []

        # we resolve symlinks and use a set in order to avoid duplicating
        # scenarios when symlinks are used.
        files = {
            path.realpath(f)
            for f in glob.glob(
                f"{self.directory}/**/molecule/*/molecule.yml", recursive=True
            )
        }

        for file in files:
            # Check scenario path
            base_dir = path.dirname(file)
            # Find if it's anywhere in the ignore list
            tree = base_dir.split("/")
            ignored = False
            for branch in tree:
                if branch in self.options.ignore_paths:
                    ignored = True
            if not ignored:
                self._scenarios.append(
                    Scenario(
                        path.relpath(base_dir, self.directory),
                        self.molecule_config,
                    )
                )
        return self._scenarios

    @property
    def tox_cases(self):
        """Returns a list of TestCase objects that can be queried to create
        the structure of a test environment.

        :return: List of TestCase objects"""

        # pylint: disable=fixme
        # TODO(ssbarnea): Detect and enable only those tests that do exist
        # to avoid confusing tox user.
        ANSIBLE_TEST_COMMANDS: Dict[str, Dict[str, Any]] = {
            "integration": {
                "args": ["--requirements"],
                "requires": "tests/integration",
            },
            "network-integration": {
                "args": ["--requirements"],
                "requires": "tests/network-integration",
            },
            # sanity tests do not need presence of sanity check or even tests
            # folder
            "sanity": {"args": ["--requirements"], "requires": ""},
            "shell": {"args": ["--requirements"]},
            "units": {
                "args": ["--requirements"],
                "requires": "tests/unit",
            },
            "windows-integration": {
                "args": ["--requirements"],
                "requires": "tests/windows-integration",
            },
            # special commands (not supported by us yet)
            "coverage": {"requires": "tests/unit"},
            "env": {},
        }

        # Append posargs if any to each command
        for value in ANSIBLE_TEST_COMMANDS.values():
            if "args" not in value:
                value["args"] = copy.deepcopy(self.tox.posargs)
            else:
                value["args"].extend(self.tox.posargs)
            if "--python" not in self.tox.posargs:
                value["args"].extend(
                    ["--python", f"{sys.version_info[0]}.{sys.version_info[1]}"]
                )

        tox_cases = []
        drivers = {s.driver for s in self.scenarios if s.driver}
        for scenario in self.scenarios:
            tox_cases.append(ToxMoleculeCase(scenario, drivers=drivers))

        # if we are inside a collection, we also enable ansible-test support
        galaxy_file = path.join(self.directory, "galaxy.yml")
        if path.isfile(galaxy_file):
            galaxy_config = load_yaml(galaxy_file)
            for command in ANSIBLE_TEST_COMMANDS:
                if not path.exists(
                    path.join(
                        self.directory,
                        ANSIBLE_TEST_COMMANDS[command].get("requires", ""),
                    )
                ):
                    continue
                try:
                    tox_cases.append(
                        ToxAnsibleTestCase(
                            command,
                            args=ANSIBLE_TEST_COMMANDS[command]["args"],
                            galaxy_config=galaxy_config,
                        )
                    )
                except RuntimeError as exc:
                    logging.warning(str(exc))

        tox_cases.append(ToxLintCase(tox_cases))
        return tox_cases
