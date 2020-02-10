from .tox_base_case import ToxBaseCase
from copy import copy


BASH = "cd {} && molecule {} lint -s {}"


class ToxLintCase(ToxBaseCase):
    def __init__(self, cases, name_factors=[]):
        self._cases = copy(cases)
        self._name_factors = name_factors + ['lint_all']
        super(ToxLintCase, self).__init__()

    def get_commands(self, options):
        cmds = []
        for case in self._cases:
            if case == self:
                continue
            molecule_options = " ".join(options.get_global_opts())
            cmd = ["bash", "-c", BASH.format(case.role.directory,
                                             molecule_options,
                                             case.scenario.name)]
            cmds.append(cmd)
        return cmds

    def get_working_dir(self):
        return '{toxinidir}'

    def get_dependencies(self):
        return ["molecule"]

    def get_name(self):
        return '-'.join(self._name_factors)
