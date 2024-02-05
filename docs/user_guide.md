# Usage of tox-ansible

From the root of your collection, create an empty `tox-ansible.ini` file and list the available environments:

```bash
touch tox-ansible.ini
tox list --ansible --conf tox-ansible.ini
```

A list of dynamically generated Ansible environments will be displayed:

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

These represent the available testing environments. Each denotes the type of tests that will be run, the Python interpreter used to run the tests, and the Ansible version used to run the tests.

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
Note: The specific Python interpreter will need to be pre-installed on your system, e.g.:

```bash
sudo dnf install python3.10
```

To review the specific commands and configuration for each of the integration, sanity, and unit factors:

```bash
tox config --ansible --conf tox-ansible.ini
```

Generate specific GitHub action matrix as per scope mentioned with `--matrix-scope`:

```bash
tox --ansible --gh-matrix --matrix-scope unit --conf tox-ansible.ini
```

A list of dynamically generated Ansible environments will be displayed specifically for unit tests:

```
[
  {
    "description": "Unit tests using ansible 2.9 and python 3.8",
    "factors": [
      "unit",
      "py3.8",
      "2.9"
    ],
    "name": "unit-py3.8-2.9",
    "python": "3.8"
  },
  ...
  {
    "description": "Unit tests using ansible-core milestone and python 3.12",
    "factors": [
      "unit",
      "py3.12",
      "milestone"
    ],
    "name": "unit-py3.12-milestone",
    "python": "3.12"
  }
]
```

## Passing command line arguments to ansible-test / pytest

The behavior of the `ansible-test` (for `sanity-*` environments) or `pytest` (for `unit-*` and `integration-*` environments) commands can be customized by passing further command line arguments to it, e.g., by invoking `tox` like this:

```bash
tox -f sanity --ansible --conf tox-ansible.ini -- --test validate-modules -vvv
```

The arguments after the `--` will be passed to the `ansible-test` command. Thus in this example, only the `validate-modules` sanity test will run, but with an increased verbosity.

Same can be done to pass arguments to the `pytest` commands for the `unit-*` and `integration-*` environments:

```bash
tox -e unit-py3.11-2.15 --ansible --conf tox-ansible.ini -- --junit-xml=tests/output/junit/unit.xml
```

## Usage in a CI/CD pipeline

The repo contains a GitHub workflow that can be used in a GitHub actions CI/CD pipeline. The workflow will run all tests across all available environments unless limited by the `skip` option in the `tox-ansible.ini` file.

Each environment will be run in a separate job. The workflow will run all jobs in parallel.

The GitHub matrix is dynamically created by `tox-ansible` using the `--gh-matrix` and `--ansible` flags. The list of environments is converted to a list of entries in json format and added to the file specified by the "GITHUB_OUTPUT" environment variable. The workflow will read this file and use it to create the matrix.

A sample use of the GitHub workflow might look like this:

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
    uses: ansible/tox-ansible/.github/workflows/run.yml@main
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

Although the `tox-ansible` plugin does not have functionality specific to molecule, it can be a powerful tool to run `molecule` scenarios across a matrix of Ansible and Python versions.

This can be accomplished by presenting molecule scenarios as integration tests available through `pytest` using the [pytest-ansible](https://github.com/ansible-community/pytest-ansible) plugin, which is installed when `tox-ansible` is installed.

Assuming the following collection directory structure:

```bash
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
│   │   └── module.py
├── tests
│   ├── integration
│   │   │── targets
│   │   │   ├── success
│   │   │   │   └── tasks
│   │   │   │       └── main.yaml
│   │   └── test_integration.py
├── tox-ansible.ini
└── tox.ini
```

Individual `molecule` scenarios can be added to the collection's extension directory to test playbooks, roles, and integration targets.

In order to present each `molecule` scenario as an individual `pytest` test a new `helper` file is added.

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
