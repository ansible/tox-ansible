# tox-ansible

## Introduction

`tox-ansible` is a utility designed to simplify the testing of ansible content collections.

Implemented as `tox` plugin, `tox-ansible` provides a simple way to test ansible content collections across multiple python interpreter and ansible versions.

`tox-ansible` uses familiar python testing tools to perform the actual testing. It uses `tox` to create and manage the testing environments, `ansible-test sanity` to run the sanity tests, and `pytest` to run the unit and integration tests. This eliminated the black box nature of other approaches and allows for more control over the testing process.

When used on a local development system, each of the environments are left intact after a test run. This allows for easy debugging of failed tests for a given test type, python interpreter and ansible version.

By using `tox` to create and manage the testing environments, Test outcomes should always be the same on a local development system as they are in a CI/CD pipeline.

`tox` virtual environments are created in the `.tox` directory. These are easily deleted and recreated if needed.

## Installation

Install from pypi:

```bash
pip install tox-ansible
```

## Dependencies

`tox-ansible` will install additional dependencies if necessary:

- `tox` version 4.0 or greater.
- `pytest-ansible` version 3.1.0 or greater.
- `pytest`
- `pytest-xdist`
- `pyyaml`

## Usage

From the root of your collection, create an empty `tox-ansible.ini` file and list the available environments:

```bash
touch tox-ansible.ini
tox list --ansible --conf tox-ansible.ini
```

A list of dynamically generated ansible environments will be displayed:

```

default environments:
...
integration-py3.11-2.14      -> Integration tests for ansible.scm using ansible-core 2.14 and python 3.11
integration-py3.11-devel     -> Integration tests for ansible.scm using ansible-core devel and python 3.11
integration-py3.11-milestone -> Integration tests for ansible.scm using ansible-core milestone and python 3.11
...
sanity-py3.11-2.14           -> Sanity tests for ansible.scm using ansible-core 2.14 and python 3.11
sanity-py3.11-devel          -> Sanity tests for ansible.scm using ansible-core devel and python 3.11
sanity-py3.11-milestone      -> Sanity tests for ansible.scm using ansible-core milestone and python 3.11
...
unit-py3.11-2.14             -> Unit tests for ansible.scm using ansible-core 2.14 and python 3.11
unit-py3.11-devel            -> Unit tests for ansible.scm using ansible-core devel and python 3.11
unit-py3.11-milestone        -> Unit tests for ansible.scm using ansible-core milestone and python 3.11
```

These represent the testing environments that are available. Each denotes the type of tests that will be run, the python interpreter used to run the tests, and the ansible version used to run the tests.

To run tests with a single environment, simply run the following command:

```bash
tox -e sanity-py3.11-2.14 --ansible --conf tox-ansible.ini
```

To run tests with multiple environments, simply add the environment names to the command:

```bash
tox -e sanity-py3.11-2.14,unit-py3.11-2.14 --ansible --conf tox-ansible.ini
```

To run all tests of a specific type in all available environments, use the factor `-f` flag:

```bash
tox -f unit --ansible -p auto --conf tox-ansible.ini
```

To run all tests across all available environments:

```bash
tox --ansible -p auto --conf tox-ansible.ini
```

Note: The `-p auto` flag will run multiple tests in parallel.
Note: The specific python interpreter will need to be pre-installed on you system, e.g.:

```bash
sudo dnf install python3.9
```

To review the specific commands and configuration for each of the integration, sanity, and unit factors:

```bash
tox config --ansible --conf tox-ansible.ini
```

## Configuration

`tox-ansible` should be configured using a `tox-ansible.ini` file. Using a `tox-ansible.ini` file allows for the introduction of the `tox-ansible` plugin to a repository that may already have an existing `tox` configuration without conflicts. If no configuration overrides are needed, the `tox-ansible.ini` file may be empty, but should be present. In addition to all `tox` supported keywords the `ansible` section and `skip` keyword is available:

```ini
# tox-ansible.ini
[ansible]
skip =
    2.9
    devel
```

This will skip tests in any environment that use ansible 2.9 or the devel branch. The list of strings are used for a simple string in string comparison of environment names.

## Overriding the configuration

Any configuration in either the `[testenv]` section or am environment section `[testenv:integration-py3.11-{devel,milestone}]` can override some or all of the `tox-ansible` environment configurations.

For example

```ini

[testenv]
commands_pre =
    true

[testenv:integration-py3.11-{devel,milestone}]
commands =
    true
```

will result in:

```ini
# tox-ansible.ini
[testenv:integration-py3.11-devel]
commands_pre = true
commands = true
```

Used without caution, this configuration can result in unexpected behavior, and possible false positive or false negative test results.

## Usage in a CI/CD pipeline

The repo contains a github workflow that can be used in a github actions CI/CD pipeline. The workflow will run all tests across all available environments, unless limited by the `skip` option in the `tox-ansible.ini` file.

Each environment will be run in a separate job. The workflow will run all jobs in parallel.

The github matrix is dynamically created by `tox-ansible` using the `--gh-matrix` and `--ansible` flags. The list of environments is converted to a list of entries in json format and added the file specified by the "GITHUB_OUTPUT" environment variable. The workflow will read this file and use it to create the matrix.

A sample use of the github workflow might look like this:

```yaml
name: Test collection

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

on:
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  tox-ansible:
    uses: tox-dev/tox-ansible/.github/workflows/run.yml@main
```

Sample `json`

```json
[
  // ...
  {
    "description": "Integration tests using ansible-core devel and python 3.11",
    "factors": ["integration", "py3.11", "devel"],
    "name": "integration-py3.11-devel",
    "python": "3.11"
  }
  // ...
]
```

## Testing molecule scenarios

Although the `tox-ansible` plugin does not have functionality specific to molecule, it can be a powerful tool to run `molecule` scenarios across a matrix of ansible and python versions.

This can be accomplished by presenting molecule scenarios as integration tests available through `pytest` using the [pytest-ansible](https://github.com/ansible-community/pytest-ansible) plugin, which is installed when `tox-ansible` is installed.

Assuming the following collection directory structure:

```
namespace.name
├── extensions
│   ├── molecule
│   │   ├── playbook
│   │   │   ├── create.yml
│   │   │   ├── converge.yml
│   │   │   ├── molecule.yml
│   │   │   └── verify.yml
│   │   ├── plugins
│   │   │   ├── create.yml
│   │   │   ├── converge.yml
│   │   │   ├── molecule.yml
│   │   │   └── verify.yml
│   │   ├── targets
│   │   │   ├── create.yml
│   │   │   ├── converge.yml
│   │   │   ├── molecule.yml
│   │   │   └── verify.yml
├── playbooks
│   └── site.yaml
├── plugins
│   ├── action
│   │   └── action_plugin.py
│   ├── modules
│   │   └── action_plugin.py
├── tests
│   ├── integration
|   |   ├── targets
│   │   │   ├── success
│   │   │   │   └── tasks
│   │   │   │       └── main.yaml
│   │   └── test_integration.py
├── tox-ansible.ini
└── tox.ini
```

Individual `molecule` scenarios can be added to the collection's extension directory to test playbooks, roles, and integration targets.

In order to present each `molecule` sceario as an invididual `pytest` test a new `helper` file is added.

```python
# tests/integration/test_integration.py

"""Tests for molecule scenarios."""
from __future__ import absolute_import, division, print_function

from pytest_ansible.molecule import MoleculeScenario


def test_integration(molecule_scenario: MoleculeScenario) -> None:
    """Run molecule for each scenario.

    :param molecule_scenario: The molecule scenario object
    """
    proc = molecule_scenario.test()
    assert proc.returncode == 0
```

The `molecule_scenario` fixture parametrizes the `molecule` scenarios found within the collection and creates an individual `pytest` test for each which will be run during any `integration-*` environment.

This approach provides the flexibility of running the `molecule` scenarios directly with `molecule`, `pytest` or `tox`. Additionally, presented as native `pytest` tests, the `molecule` scenarios should show in the `pytest` test tree in the user's IDE.

## How does it work?

`tox` will, by default, create a python virtual environment for a given environment. `tox-ansible` adds ansible collection specific build and test logic to tox. The collection is copied into the virtual environment created by tox, built, and installed into the virtual environment. The installation of the collection will include the collection's collection dependencies. `tox-ansible` will also install any python dependencies from a `test-requirements.txt` and `requirements.txt` file. The virtual environment's temporary directory is used, so the copy, build and install steps are performed with each test run ensuring the current collection code is used.

`tox-ansible` also sets the `ANSIBLE_COLLECTIONS_PATH` environment variable to point to the virtual environment's temporary directory. This ensures that the collection under test is used when running tests. The `pytest-ansible-units` pytest plugin injects the `ANSIBLE_COLLECTIONS_PATH` environment variable into the collection loader so ansible-core can locate the collection.

`pytest` is ued to run both the `unit` and `integration tests`.
`ansible-test sanity` is used to run the `sanity` tests.

For a full configuration examples for each of the sanity, integration, and unit tests including the commands being run and the environments variables being set and passed, see the following:

- [integration](docs/integration.ini)
- [sanity](docs/sanity.ini)
- [unit](docs/unit.ini)

See the [tox documentation](https://tox.readthedocs.io/en/latest/) for more information on tox.

## Note to version 1.x users

Users of tox-ansible v1 should use the stable/1.x branch because the default branch is a rewrite of the plugin for tox 4.0+ which is not backward compatible with the old plugin.

Version 1 of the plugin had native support for molecule. Please see the "Running molecule scnearios" above for an alternative approach.

## License

MIT
