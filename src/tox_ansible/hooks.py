"""Tox hook implementations."""
from __future__ import print_function

import logging
import sys

try:
    from tox import hookimpl

    from tox_ansible import tox_helper
    from tox_ansible.ansible import Ansible
    from tox_ansible.filter import Filter
    from tox_ansible.options import (
        DRIVER_ENV_NAME,
        DRIVER_OPTION_NAME,
        SCENARIO_ENV_NAME,
        SCENARIO_OPTION_NAME,
        Options,
    )

    @hookimpl
    def tox_addoption(parser):
        """Add options to filter down to only executing the given roles and
        scenarios."""
        parser.add_argument(
            "--ansible-scenario",
            dest=SCENARIO_OPTION_NAME,
            action="append",
            help="Only execute scenarios with the given names (env {})".format(
                SCENARIO_ENV_NAME
            ),
        )
        parser.add_argument(
            "--ansible-driver",
            dest=DRIVER_OPTION_NAME,
            action="append",
            help="Only execute scenarios with the given driver (env {})".format(
                DRIVER_ENV_NAME
            ),
        )

    @hookimpl
    def tox_configure(config):
        """If the current folder includes a file named `galaxy.yml`, then look for
        a roles directory and generate environments for every (role, scenario)
        combo that is discovered therein."""
        tox = tox_helper.Tox(config)
        options = Options(tox)
        ansible = Ansible(options=options, base=tox.toxinidir)

        # Only execute inside of a collection, otherwise we have nothing to do
        if not ansible.is_ansible:
            return

        # Create any test cases that are discovered in the directory structure and
        # expand them per any configured matrix axes in the config file
        tox_cases = ansible.tox_cases
        tox_cases = options.expand_matrix(tox_cases)

        # Add them to the envconfig list before testing for explicit calls, because
        # we want the user to be able to specifically state an auto-generated
        # test, if they want to
        tox.add_envconfigs(tox_cases, options)

        # Don't filter down or add to envlist if an environment has been
        # specified by the user
        if hasattr(config, "envlist_explicit") and config.envlist_explicit:
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
        config.envlist.sort()
        config.envlist_default = config.envlist
        if len(config.envlist) == 0:
            print("****** No environments matched. This is a problem.")
            sys.exit(101)


except ImportError:
    # tox4
    logging.error("tox-ansible disabled itself as it does not support tox4 yet.")
