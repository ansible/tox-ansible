import os
import tox
from copy import deepcopy
from itertools import chain
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
INI_ANSIBLE_VERSIONS = "ansible"
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

    def filter_envlist(self, envs):
        """Filters a list of environments to match the arguments already
        provided to this code."""
        if self.role:
            def filter_role(e):
                if hasattr(e[1], 'scenario'):
                    return e[1].scenario.role.folder in self.role
                return False
            envs = dict(filter(filter_role, envs.items()))
        if self.scenario:
            def filter_scenario(e):
                if hasattr(e[1], 'scenario'):
                    return e[1].scenario.name in self.scenario
                return False
            envs = dict(filter(filter_scenario, envs.items()))
        return envs

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
        def base_python(env, version):
            env['basepython'] = 'python' + version
        return self._matrix(envs, INI_PYTHON_VERSIONS, 'py', base_python)

    def ansible_matrix(self, envs):
        def ansible_dep(env, version):
            env['deps'].append('ansible=={}.*'.format(version))
        return self._matrix(envs, INI_ANSIBLE_VERSIONS, 'ansible', ansible_dep)

    def get_global_opts(self):
        opts = self.reader.getlist(INI_MOLECULE_GLOBAL_OPTS, sep="\n")
        return opts

    def _parse_opt(self, option, opt, env):
        if option[opt] is not None:
            values = list(map(lambda a: a.split(','), option[opt]))
            values = list(chain.from_iterable(values))
            return values

        if env in os.environ:
            return os.environ[env].split(',')

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

    def _matrix(self, envs, opt, factor, callback=lambda e: e):
        versions = self.reader.getlist(opt, sep=" ")
        if not versions:
            return envs
        results = []
        for e in envs:
            for version in versions:
                env = deepcopy(e)
                env['name'].insert(0, factor + version.replace('.', ''))
                callback(env, version)
                results.append(env)
        return results
