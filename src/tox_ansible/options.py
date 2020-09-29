import os
from itertools import chain

from .matrix import Matrix
from .matrix.axes import AnsibleAxis, PythonAxis

SCENARIO_OPTION_NAME = "ansible_scenario"
DRIVER_OPTION_NAME = "ansible_driver"

SCENARIO_ENV_NAME = "TOX_" + SCENARIO_OPTION_NAME.upper()
DRIVER_ENV_NAME = "TOX_" + DRIVER_OPTION_NAME.upper()

INI_SECTION = "ansible"
INI_PYTHON_VERSIONS = "python"
INI_ANSIBLE_VERSIONS = "ansible"
INI_MOLECULE_GLOBAL_OPTS = "molecule_opts"
INI_IGNORE_PATHS = "ignore_path"


class Options(object):
    """Represents the options, and performs the logic around them."""

    def __init__(self, tox):
        self.tox = tox
        self.reader = tox.get_reader(INI_SECTION)
        opts = tox.get_opts()
        self.scenario = self._parse_opt(opts, SCENARIO_OPTION_NAME, SCENARIO_ENV_NAME)
        self.driver = self._parse_opt(opts, DRIVER_OPTION_NAME, DRIVER_ENV_NAME)
        self.matrix = Matrix()

        ansible = self.reader.getlist(INI_ANSIBLE_VERSIONS, sep=" ")
        if ansible:
            self.matrix.add_axis(AnsibleAxis(ansible))
        pythons = self.reader.getlist(INI_PYTHON_VERSIONS, sep=" ")
        if pythons:
            self.matrix.add_axis(PythonAxis(pythons))

    def expand_matrix(self, tox_cases):
        """Expand the tox_cases list if there are any matrix factors defined
        to be expanded. Return the list of resulting types.

        :param tox_cases: An iterable of test case objects
        :return: A list of test cases expanded per any configured matrix
        values"""
        return self.matrix.expand(tox_cases)

    def do_filter(self):
        """Determine if we should be filtering or not. Only do so if there are
        arguments to do the filtering around. Otherwise, we don't want to leave
        no environments to execute against."""
        return len(self.scenario) != 0 or len(self.driver) != 0

    def get_global_opts(self):
        opts = self.reader.getlist(INI_MOLECULE_GLOBAL_OPTS, sep="\n")
        return opts

    @property
    def ignore_paths(self):
        paths = self.reader.getlist(INI_IGNORE_PATHS, sep="\n")
        return paths

    def _parse_opt(self, option, opt, env):
        if isinstance(option, dict) and option[opt] is not None:
            values = list(map(lambda a: a.split(","), option[opt]))
            values = list(chain.from_iterable(values))
            return values

        if env in os.environ:
            return os.environ[env].split(",")

        return []
