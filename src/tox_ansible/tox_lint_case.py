from copy import copy

from .tox_base_case import ToxBaseCase
from .tox_helper import Tox

BASH = "cd {} && molecule {} lint -s {}"


class ToxLintCase(ToxBaseCase):
    def __init__(self, cases, name_parts=None):
        self._cases = copy(cases)
        self._name_parts = name_parts or []
        self._config = Tox()
        super().__init__()

    def get_commands(self, options):
        cmds = []
        for case in self._cases:
            # Cases not supporting scenario are to be ignored
            if not hasattr(case, "scenario"):
                continue
            molecule_options = " ".join(options.get_global_opts())
            cmd = [
                "bash",
                "-c",
                BASH.format(
                    self._config.toxinidir.join(case.scenario.run_dir),
                    molecule_options,
                    case.scenario.name,
                ),
            ]
            cmds.append(cmd)
        return cmds

    def get_working_dir(self):
        return self._config.toxinidir

    def get_dependencies(self):
        deps = set(["molecule", "flake8", "ansible-lint", "yamllint"])
        for case in self._cases:
            if hasattr(case, "scenario") and case.scenario.driver != "delegated":
                deps.add("molecule-{}".format(case.scenario.driver))
        return deps

    def get_name(self):
        return "-".join(self._name_parts + ["lint_all"])

    @property
    def description(self):
        return "Auto-generated environment to run: molecule lint on all scenarios"
