from os import path, walk

from ..tox_lint_case import ToxLintCase
from ..tox_test_case import ToxTestCase
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

        :param base: Path to the folder. Defaluts to being relative to
        os.path.curdir, but can be absolute"""
        self.directory = path.abspath(path.join(path.curdir, base))
        self._scenarios = None
        self.options = options

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
        for folder, dirs, files in walk(self.directory):
            tree = folder.split(path.sep)
            # Find if it's anywhere in the ignore list
            ignored = False
            for branch in tree:
                if branch in self.options.ignore_paths:
                    ignored = True
            if (
                not ignored
                and len(tree) >= 2
                and tree[-2] == "molecule"
                and "molecule.yml" in files
            ):
                self._scenarios.append(Scenario(path.relpath(folder, self.directory)))
        return self._scenarios

    @property
    def tox_cases(self):
        """Returns a list of TestCase objects that can be queried to create
        the structure of a test environment.

        :return: List of TestCase objects"""
        tox_cases = []
        for scenario in self.scenarios:
            tox_cases.append(ToxTestCase(scenario))
        tox_cases.append(ToxLintCase(tox_cases))
        return tox_cases
