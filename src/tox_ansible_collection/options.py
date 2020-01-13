import os
import tox
from copy import deepcopy
from .envs import customize_env


ROLE_OPTION_NAME = 'ansible_role'
SCENARIO_OPTION_NAME = 'ansible_scenario'
DRIVER_OPTION_NAME = 'ansible_driver'

ROLE_ENV_NAME = 'TOX_' + ROLE_OPTION_NAME.upper()
SCENARIO_ENV_NAME = 'TOX_' + SCENARIO_OPTION_NAME.upper()
DRIVER_ENV_NAME = 'TOX_' + DRIVER_OPTION_NAME.upper()

DEPS = ['molecule', 'shade', 'docker']

INI_SECTION = "ansible"
INI_PYTHON_VERSIONS = "python"
INI_MOLECULE_GLOBAL_OPTS = "molecule_opts"


class Options(object):
    """Represents the options, and performs the logic around them."""
    def __init__(self, config):
        self.config = config
        self.reader = self._get_reader(INI_SECTION, self.config._cfg)
        opts = vars(config.option)
        self.role = self._parse_opt(opts, ROLE_OPTION_NAME, ROLE_ENV_NAME)
        self.scenario = self._parse_opt(opts, SCENARIO_OPTION_NAME,
                                        SCENARIO_ENV_NAME)
        self.driver = self._parse_opt(opts, DRIVER_OPTION_NAME,
                                      DRIVER_ENV_NAME)

    def _parse_opt(self, option, opt, env):
        if option[opt] is not None:
            return option[opt]

        if env in os.environ:
            return os.environ[env]

        return None

    def _get_reader(self, section, cfg, prefix=None):
        """Creates a SectionReader and configures it with known and reasonable
        substitution values based on the config."""
        reader = tox.config.SectionReader(section, cfg, prefix=prefix)
        distshare_default = "{homedir}/.tox/distshare"
        reader.addsubstitutions(toxinidir=self.config.toxinidir,
                                homedir=self.config.homedir,
                                toxworkdir=self.config.toxworkdir)
        self.config.distdir = reader.getpath("distdir", "{toxworkdir}/dist")
        reader.addsubstitutions(distdir=self.config.distdir)
        self.config.distshare = reader.getpath("distshare", distshare_default)
        reader.addsubstitutions(distshare=self.config.distshare)
        return reader

    def get_envs(self, scenario):
        """Creates a set of environments for the given scenario, based on
        its name, its role name, and any configured matrix expansion values,
        such as python versions, ansible versions, and more

        Returns an iterable list of such configurations."""
        # Stripped down version of parseini.__init__ for making a generated
        # envconfig
        prefix = 'tox' if self.config.toxinipath.basename == 'setup.cfg' \
            else None
        reader = self._get_reader("tox", self.config._cfg, prefix=prefix)
        try:
            make_envconfig = tox.config.ParseIni.make_envconfig  # tox 3.4.0+
        except AttributeError:
            make_envconfig = tox.config.parseini.make_envconfig
        # Python 2 fix
        make_envconfig = getattr(make_envconfig, '__func__', make_envconfig)

        # Identify which environments to create
        envs = [{'name': [scenario.role.folder, scenario.name],
                 'scenario': scenario, 'deps': DEPS}]
        envs = self.ansible_matrix(envs)
        envs = self.python_matrix(envs)

        envconfigs = {}
        for env in envs:
            envname = '-'.join(env['name'])
            section = tox.config.testenvprefix + envname
            envconfig = make_envconfig(self.config, envname, section,
                                       reader._subs, self.config)
            customize_env(envconfig, env, self)
            envconfigs[envname] = envconfig
        return envconfigs

    def python_matrix(self, envs):
        python = self.reader.getlist(INI_PYTHON_VERSIONS, sep=" ")
        if not python:
            return envs
        results = []
        for e in envs:
            for py in python:
                env = deepcopy(e)
                env['name'].insert(0, 'py' + py.replace('.', ''))
                env['basepython'] = 'python' + py
                results.append(env)
        return results

    def ansible_matrix(self, envs):
        # TODO: multiply envs by ansible versions, if necessary
        return envs

    def get_global_opts(self):
        opts = self.reader.getlist(INI_MOLECULE_GLOBAL_OPTS, sep="\n")
        return opts
