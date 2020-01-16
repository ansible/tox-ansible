from os import path, walk, sep
from ..tox_case_base import ToxCaseBase
from .scenario import Scenario


class Role(object):
    """Knows things about an Ansible role and how it is stored."""
    def __init__(self, directory):
        """Initialize a potential role candidate.

        :param directory: The path to what might be a role directory"""
        self.directory = directory
        # TODO: It is not always the case - we could parse the YAML of the
        # meta/main.yml to find out what the actual name is, but for the
        # moment this is the default, and we can live with it
        self.name = path.basename(self.directory)

    def __str__(self):
        return self.name

    def is_role(self):
        """Tells you if this folder is actually a role.

        :return: True if the path is an Ansible role. False otherwise"""
        # Only the tasks/main.yml file is required for a role, although
        # there is often much more to it
        return path.isdir(self.directory) and \
            path.isfile(path.join(self.directory, "tasks", "main.yml"))

    def get_scenarios(self):
        scenarios = []
        for folder, dirs, files in walk(self.directory):
            tree = folder.split(sep)
            if len(tree) >= 2 and tree[-2] == "molecule" \
               and 'molecule.yml' in files:
                scenarios.append(Scenario(path.join(self.directory, folder)))
        return scenarios

    def get_tox_cases(self):
        """Fetch back every test case for every scenario that is present
        in this role.

        :return: A list of test cases"""
        tox_cases = []
        for scenario in self.get_scenarios():
            tox_cases.append(ToxCaseBase(self, scenario))
        return tox_cases
