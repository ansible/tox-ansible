from copy import copy
from pathlib import Path

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
        if self.is_precommit:
            cmds = [["pre-commit", "run", "--all"]]
        else:
            cmds = []
            # Construct the ansible-lint command
            ansible_lint = ["ansible-lint", "-R"]
            if options.ansible_lint:
                ansible_lint.append("-c")
                ansible_lint.append(options.ansible_lint)
            cmds.append(ansible_lint)

            # Construct the yamllint command
            if options.yamllint:
                yamllint = ["yamllint", "-c", options.yamllint, "."]
                cmds.append(yamllint)

            # Construct the flake8 invocation
            flake8 = ["flake8", "."]
            cmds.append(flake8)

        return cmds

    @property
    def is_precommit(self) -> bool:
        """Determines if this repository is configured to use pre-commit
        or not."""
        p = Path(self.working_dir) / ".pre-commit-config.yaml"
        return p.exists()

    @property
    def working_dir(self):
        return self._config.toxinidir

    @property
    def dependencies(self):
        if self.is_precommit:
            deps = set(["pre-commit"])
        else:
            deps = set(["flake8", "ansible-lint", "yamllint", "ansible"])
        return deps

    def get_name(self, fmt=""):
        return "-".join(self._name_parts + ["lint_all"])
