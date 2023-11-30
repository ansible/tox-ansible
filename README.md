# tox-ansible

## Introduction

`tox-ansible` is a utility designed to simplify the testing of Ansible content collections.

Implemented as `tox` plugin, `tox-ansible` provides a simple way to test Ansible content collections across multiple Python interpreters and Ansible versions.

`tox-ansible` uses familiar python testing tools to perform the actual testing. It uses `tox` to create and manage the testing environments, `ansible-test sanity` to run the sanity tests, and `pytest` to run the unit and integration tests. This eliminated the black box nature of other approaches and allowed for more control over the testing process.

When used on a local development system, each of the environments are left intact after a test run. This allows for easy debugging of failed tests for a given test type, python interpreter and Ansible version.

By using `tox` to create and manage the testing environments, Test outcomes should always be the same on a local development system as they are in a CI/CD pipeline.

`tox` virtual environments are created in the `.tox` directory. These are easily deleted and recreated if needed.

## Installation

Install from pypi:

```bash
pip install tox-ansible
```

## Usage

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
sudo dnf install python3.9
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

## Configuration

`tox-ansible` should be configured using a `tox-ansible.ini` file. Using a `tox-ansible.ini` file allows for the introduction of the `tox-ansible` plugin to a repository that may already have an existing `tox` configuration without conflicts. If no configuration overrides are needed, the `tox-ansible.ini` file may be empty but should be present. In addition to all `tox` supported keywords the `ansible` section and `skip` keyword are available:

```ini
# tox-ansible.ini
[ansible]
skip =
    2.9
    devel
```

This will skip tests in any environment that uses Ansible 2.9 or the devel branch. The list of strings is used for a simple string in string comparison of environment names.

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

## How does it work?

`tox` will, by default, create a Python virtual environment for a given environment. `tox-ansible` adds Ansible collection specific build and test logic to tox. The collection is copied into the virtual environment created by tox, built, and installed into the virtual environment. The installation of the collection will include the collection's collection dependencies. `tox-ansible` will also install any Python dependencies from a `test-requirements.txt` (or `requirements-test.txt`) and `requirements.txt` file. The virtual environment's temporary directory is used, so the copy, build and install steps are performed with each test run ensuring the current collection code is used.

`tox-ansible` also sets the `ANSIBLE_COLLECTIONS_PATH` environment variable to point to the virtual environment's temporary directory. This ensures that the collection under test is used when running tests. The `pytest-ansible-units` pytest plugin injects the `ANSIBLE_COLLECTIONS_PATH` environment variable into the collection loader so ansible-core can locate the collection.

`pytest` is ued to run both the `unit` and `integration tests`.
`ansible-test sanity` is used to run the `sanity` tests.

For full configuration examples for each of the sanity, integration, and unit tests including the commands being run and the environment variables being set and passed, see the following:

- [integration](docs/integration.ini)
- [sanity](docs/sanity.ini)
- [unit](docs/unit.ini)

See the [tox documentation](https://tox.readthedocs.io/en/latest/) for more information on tox.

## Note to version 1.x users

Users of tox-ansible v1 should use the stable/1.x branch because the default branch is a rewrite of the plugin for tox 4.0+ which is not backward compatible with the old plugin.

Version 1 of the plugin had native support for molecule. Please see the "Running molecule scenarios" above for an alternative approach.

## License

MIT
