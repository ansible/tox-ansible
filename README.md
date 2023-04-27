[![CI/CD Builds](https://github.com/tox-dev/tox-ansible/workflows/tox/badge.svg)](https://github.com/tox-dev/tox-ansible/actions)
[![codecov](https://codecov.io/gh/tox-dev/tox-ansible/branch/main/graph/badge.svg)](https://codecov.io/gh/tox-dev/tox-ansible)
[![PyPI version](https://badge.fury.io/py/tox-ansible.svg)](https://badge.fury.io/py/tox-ansible)

Users of tox-ansible v1 should read [stable/1.x](https://github.com/tox-dev/tox-ansible/tree/stable/1.x#readme)
because the default branch is a rewrite of the plugin for tox 4.0+ which is
backward compatible with the old plugin.

The rewritten plugin will feature additional options for facilitating
running tests of any repository with Ansible content:

- Ability to run molecule scenarios
- Close-to-zero configuration goals
- Focus on testing collections
