"""Tox hook implementations."""
from __future__ import print_function
import os
import tox
from .ansible import Collection
from .compat import TOX_PARALLEL_ENV
from .options import (
    ROLE_OPTION_NAME,
    SCENARIO_OPTION_NAME,
    DRIVER_OPTION_NAME,

    ROLE_ENV_NAME,
    SCENARIO_ENV_NAME,
    DRIVER_ENV_NAME,

    Options
)


@tox.hookimpl
def tox_addoption(parser):
    """Add options to filter down to only executing the given roles and
    scenarios."""
    parser.add_argument(
        '--ansible-role', dest=ROLE_OPTION_NAME, action='append',
        help='Only execute molecule in the given roles (env {})'
        .format(ROLE_ENV_NAME))
    parser.add_argument(
        '--ansible-scenario', dest=SCENARIO_OPTION_NAME, action='append',
        help='Only execute scenarios with the given names (env {})'
        .format(SCENARIO_ENV_NAME))
    parser.add_argument(
        '--ansible-driver', dest=DRIVER_OPTION_NAME, action='append',
        help='Only execute scenarios with the given driver (env {})'
        .format(DRIVER_ENV_NAME))


@tox.hookimpl
def tox_configure(config):
    """If the current folder includes a file named `galaxy.yml`, then look for
    a roles directory and generate environments for every (role, scenario)
    combo that is discovered therein."""
    # Don't run in subprocesses when executing in parallel mode
    if TOX_PARALLEL_ENV in os.environ:
        return

    collection = Collection()

    # Only execute inside of a collection, otherwise we have nothing to do
    if not collection.is_collection():
        return

    options = Options(config)

    # Generate all the needed environments
    scenarios = []
    environments = {}
    # Find all the roles
    roles = collection.get_roles()
    # Find the scenarios in each role
    for role in roles:
        scenarios.extend(role.get_scenarios())
    # generate a tox environment for each scenario
    for scenario in scenarios:
        environments.update(options.get_envs(scenario))

    config.envconfigs.update(environments)

    # Don't filter down or add to envlist if an environment has been
    # specified by the user
    if config.envlist_explicit:
        return

    # TODO: enable filtering options
