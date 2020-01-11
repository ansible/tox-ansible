"""Tox hook implementations."""
from __future__ import print_function
import os
import tox
from .ansible import Collection


@tox.hookimpl
def tox_addoption(parser):
    """Add options to filter down to only executing the given roles and
    scenarios."""
    parser.add_argument(
        '--ansible-role', dest='ansible_role', action='append',
        help='Only execute molecule in the given roles (env TOX_ANSIBLE_ROLE)')
    parser.add_argument(
        '--ansible-scenario', dest='ansible_scenario', action='append',
        help='Only execute scenarios with the given names (env ' +
             'TOX_ANSIBLE_SCENARIO)')


@tox.hookimpl
def tox_configure(config):
    """If the current folder includes a file named `galaxy.yml`, then look for
    a roles directory and generate environments for every (role, scenario)
    combo that is discovered therein."""
    collection = Collection()

    # Only execute inside of a collection, otherwise we have nothing to do
    if not collection.is_collection():
        return

    # Don't mess with list if user has manually specified
    if 'TOXENV' not in os.environ and not config.options.env:
        scenarios = []
        environments = []
        # Find all the roles
        roles = collection.get_roles()
        # Find the scenarios in each role
        for role in roles:
            scenarios = scenarios + role.get_scenarios()
        # generate a tox environment for each scenario
        for scenario in scenarios:
            environments = environments + scenario.get_environment()
