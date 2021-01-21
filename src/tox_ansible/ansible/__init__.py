import copy
import glob
import sys
from os import path
from typing import Any, Dict

from tox_ansible._yaml import load_yaml
from tox_ansible.tox_helper import Tox

from ..tox_ansible_test_case import ToxAnsibleTestCase
from ..tox_lint_case import ToxLintCase
from ..tox_molecule_case import ToxMoleculeCase
from .scenario import Scenario


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

    @property
    def is_ansible(self):
        """Determine if the specified directory is an Ansible structure or not

        :return: True if this is an Ansible structure. False, otherwise."""
        return len(self.scenarios) > 0

    @property
    def scenarios(self):
        """Recursively searches the potential Ansible directory and looks for any
        scenario directories found.

        :return: An array of Scenario objects, empty if none are found"""
        # Don't walk the filesystem more often than necessary
        if self._scenarios is not None:
            return self._scenarios
        self._scenarios = []
        files = glob.glob(
            f"{self.directory}/**/molecule/*/molecule.yml", recursive=True
        )
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
                self._scenarios.append(Scenario(path.relpath(base_dir, self.directory)))
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
            # "coverage",
            "integration": {},
            "network-integration": {},
            "sanity": {"args": ["--requirements"]},
            "shell": {},
            "units": {},
            "windows-integration": {},
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
        for scenario in self.scenarios:
            tox_cases.append(ToxMoleculeCase(scenario))

        # if we are inside a collection, we also enable ansible-test support
        galaxy_file = path.join(self.directory, "galaxy.yml")
        if path.isfile(galaxy_file):
            galaxy_config = load_yaml(galaxy_file)
            for command in ANSIBLE_TEST_COMMANDS:
                tox_cases.append(
                    ToxAnsibleTestCase(
                        "sanity",
                        args=ANSIBLE_TEST_COMMANDS["sanity"]["args"],
                        galaxy_config=galaxy_config,
                    )
                )
            if path.isdir(path.join(self.directory, "tests", "unit")):
                for command in ["units", "coverage"]:
                    tox_cases.append(
                        ToxAnsibleTestCase(command, galaxy_config=galaxy_config)
                    )
            if path.isdir(path.join(self.directory, "tests", "integration")):
                for command in ["units", "coverage"]:
                    tox_cases.append(
                        ToxAnsibleTestCase(command, galaxy_config=galaxy_config)
                    )

        tox_cases.append(ToxLintCase(tox_cases))
        return tox_cases
