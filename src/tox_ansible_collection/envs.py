import py
from tox.config import DepOption


def customize_env(envconfig, env, options):
    # Default commands to run molecule
    if not envconfig.commands:
        envconfig.commands = _get_commands(env['scenario'], options)
    # Default deps to install molecule, etc
    if not envconfig.deps:
        do = DepOption()
        envconfig.deps = do.postprocess(envconfig, env['deps'])
    # Cannot run in {toxinidir}, which is default
    if not envconfig.envdir or envconfig.envdir == options.config.toxinidir:
        envconfig.envdir = options.config.toxworkdir.join("ansible")
    # Need to run molecule from the role directory
    if not envconfig.changedir or \
            envconfig.changedir == options.config.toxinidir:
        envconfig.changedir = py.path.local(env['scenario'].role.path)
    if not envconfig.basepython and 'basepython' in env:
        envconfig.basepython = env['basepython']


def _get_commands(scenario, options):
    """Creates the default commands that get added into the generated
    config objects.

    Returns a list of lists. Each element in the parent list is a command,
    with each element of the command being successive tokens similar as
    they might appear on the command line, but without needing to escape
    shell values."""
    molecule = ['molecule']
    molecule.extend(options.get_global_opts())
    molecule.extend(['test', '-s', scenario.name])
    return [molecule]
