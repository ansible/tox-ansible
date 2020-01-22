"""Tox hook implementations."""
from __future__ import print_function
import os
import sys
from tox import hookimpl
from .ansible import Ansible
from .tox_helper import Tox
from .compat import TOX_PARALLEL_ENV
from .filter import Filter
from .options import (
    ROLE_OPTION_NAME,
    SCENARIO_OPTION_NAME,
    DRIVER_OPTION_NAME,

    ROLE_ENV_NAME,
    SCENARIO_ENV_NAME,
    DRIVER_ENV_NAME,

    Options
)


@hookimpl
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


@hookimpl
def tox_configure(config):
    """If the current folder includes a file named `galaxy.yml`, then look for
    a roles directory and generate environments for every (role, scenario)
    combo that is discovered therein."""
    # Don't run in subprocesses when executing in parallel mode
    if TOX_PARALLEL_ENV in os.environ:
        return

    ansible = Ansible()
    tox = Tox(config)
    options = Options(tox)

    # Only execute inside of a collection, otherwise we have nothing to do
    if not ansible.is_ansible():
        return

    # Create any test cases that are discovered in the directory structure and
    # expand them per any configured matrix axes in the config file
    tox_cases = ansible.get_tox_cases()
    tox_cases = options.expand_matrix(tox_cases)

    # Add them to the envconfig list before testing for explicit calls, because
    # we want the user to be able to specifically state an auto-generated
    # test, if they want to
    tox.add_envconfigs(tox_cases, options)

    # Don't filter down or add to envlist if an environment has been
    # specified by the user
    if config.envlist_explicit:
        return

    # Add the items we generated to the envlist to be executed by default
    # Set, because there might be dupes
    config.envlist = list(set(config.envlist + config.ansible_envlist))

    # Since the user hasn't been explicit about which environments to execute
    # against, then we add the ones we've generated to the list, and then we
    # filter it
    if options.do_filter():
        envfilter = Filter(options)
        # Actually modify the envconfigs, because we don't care about ones we
        # won't be executing
        config.envconfigs = envfilter.filter(config.envconfigs)
        config.envlist = list(config.envconfigs.keys())
    config.envlist_default = config.envlist
    if len(config.envlist) == 0:
        print("****** No environments matched. This is a problem.")
        sys.exit(101)
