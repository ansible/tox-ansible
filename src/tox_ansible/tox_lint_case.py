from copy import copy

from .tox_base_case import ToxBaseCase
from .tox_helper import Tox

BASH = "cd {} && molecule {} lint -s {}"


class ToxLintCase(ToxBaseCase):

    description = "Auto-generated lint for ansible cases"

    def __init__(self, cases, name_parts=None):
        self._cases = copy(cases)
        self._name_parts = name_parts or []
        self._config = Tox()
        super().__init__()

    def get_commands(self, options):
        cmds = []
        # Construct the ansible-lint command
        ansible_lint = ["ansible-lint", "-R"]
        if options.ansible_lint:
            ansible_lint.append("-c")
            ansible_lint.append(options.ansible_lint)

        # Construct the yamllint command
        yamllint = ["yamllint"]
        if options.yamllint:
            yamllint.append("-c")
            yamllint.append(options.yamllint)
        yamllint.append(".")

        # Construct the flake8 invocation
        flake8 = ["flake8", "."]
        cmds.append(ansible_lint)
        cmds.append(yamllint)
        cmds.append(flake8)
        return cmds

    def get_working_dir(self):
        return self._config.toxinidir

    def get_dependencies(self):
        deps = set(["flake8", "ansible-lint", "yamllint", "ansible"])
        return deps

    def get_name(self, fmt=""):
        return "-".join(self._name_parts + ["lint_all"])
