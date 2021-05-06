import os
from itertools import chain

from tox.config import _split_env

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
INI_ANSIBLE_LINT_CONFIG = "ansible_lint_config"
INI_YAMLLINT_CONFIG = "yamllint_config"
INI_MOLECULE_CONFIG_FILES = "molecule_config_files"
INI_SCENARIO_FORMAT = "scenario_format"
INI_SCENARIO_FORMAT_DEFAULT = "$path-$parent-$name"


# pylint: disable=too-many-instance-attributes
class Options(object):
    """Represents the options, and performs the logic around them."""

    def __init__(self, tox):
        self.tox = tox
        self.reader = tox.get_reader(INI_SECTION)
        opts = tox.get_opts()
        self.scenario = self._parse_opt(opts, SCENARIO_OPTION_NAME, SCENARIO_ENV_NAME)
        self.driver = self._parse_opt(opts, DRIVER_OPTION_NAME, DRIVER_ENV_NAME)
        self.matrix = Matrix()
        self.ansible_lint = self.reader.getstring(INI_ANSIBLE_LINT_CONFIG)
        self.yamllint = self.reader.getstring(INI_YAMLLINT_CONFIG)
        self.molecule_config_files = self.reader.getlist(
            INI_MOLECULE_CONFIG_FILES, sep="\n"
        )
        self.scenario_format = self.reader.getstring(
            INI_SCENARIO_FORMAT, INI_SCENARIO_FORMAT_DEFAULT
        )

        ansible = self.reader.getlist(INI_ANSIBLE_VERSIONS)
        ansible = _split_env(ansible)
        if ansible:
            self.matrix.add_axis(AnsibleAxis(ansible))
        pythons = self.reader.getlist(INI_PYTHON_VERSIONS)
        pythons = _split_env(pythons)
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
