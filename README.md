# tox-ansible

## Note to version 1.x users

Users of tox-ansible v1 should use the stable/1.x branch because the default branch is a rewrite of the plugin for tox 4.0+ which is not backward compatible with the old plugin.

The rewritten plugin will feature additional options for facilitating running tests of any repository with Ansible content:

Ability to run molecule scenarios (planned)
Close-to-zero configuration goals (in progress)
Focus on testing collections (initial implementation)

## Introduction

`tox-ansible` is a utility designed to simplify the testing of ansible content collections.

Implemented as `tox` plugin, `tox-ansible` provides a simple way to test ansible content collections across multiple python interpreter and ansible versions.

`tox-ansible` uses familiar python testing tools to perform the actual testing. It uses `tox` to create and manage the testing environments, `ansible-test sanity` to run the sanity tests, and `pytest` to run the unit and integration tests. This eliminated the black box nature of other approaches and allows for more control over the testing process.

When used on a local development system, each of the environments are left intact after a test run. This allows for easy debugging of failed tests for a given test type, python interpreter and ansible version.

By using `tox` to create and manage the testing environments, Test outcomes should always be the same on a local development system as they are in a CI/CD pipeline.

`tox` virtual environments are created in the `.tox` directory. These are easily deleted and recreated if needed.

## Installation

Until `tox-ansible` is published to PyPI, you can install it from source:

```bash
pip install tox-ansible
```

`tox-ansible` will install `tox` as a dependency if necessary.

## Collection dependencies

Add the following to a `test-requirements.txt` file in the root of your collection:

```bash
git+https://github.com/ansible-community/pytest-ansible-units.git
```

The `pytest-ansible-units` package is required for `tox-ansible` to run unit tests.

## Usage

From the root of your collection run the following command:

```bash
tox -l --ansible
```

A list of dynamically generated ansible environments will be displayed:

```bash
integration-py3.8-2.9
integration-py3.8-2.12
integration-py3.8-2.13
integration-py3.9-2.12
integration-py3.9-2.13
integration-py3.9-2.14
integration-py3.9-devel
integration-py3.9-milestone
integration-py3.10-2.12
integration-py3.10-2.13
integration-py3.10-2.14
integration-py3.10-devel
integration-py3.10-milestone
integration-py3.11-2.14
integration-py3.11-devel
integration-py3.11-milestone
sanity-py3.8-2.9
sanity-py3.8-2.12
sanity-py3.8-2.13
sanity-py3.9-2.12
sanity-py3.9-2.13
sanity-py3.9-2.14
sanity-py3.9-devel
sanity-py3.9-milestone
sanity-py3.10-2.12
sanity-py3.10-2.13
sanity-py3.10-2.14
sanity-py3.10-devel
sanity-py3.10-milestone
sanity-py3.11-2.14
sanity-py3.11-devel
sanity-py3.11-milestone
unit-py3.8-2.9
unit-py3.8-2.12
unit-py3.8-2.13
unit-py3.9-2.12
unit-py3.9-2.13
unit-py3.9-2.14
unit-py3.9-devel
unit-py3.9-milestone
unit-py3.10-2.12
unit-py3.10-2.13
unit-py3.10-2.14
unit-py3.10-devel
unit-py3.10-milestone
unit-py3.11-2.14
unit-py3.11-devel
unit-py3.11-milestone
```

These represent the testing environments that are available to you. Each denotes the type of tests that will be run, the python interpreter used to run the tests, and the ansible version used to run the tests.

To run tests with a single environment, simply run the following command:

```bash
tox -e sanity-py3.11-2.14 --ansible
```

To run tests with multiple environments, simply add the environment names to the command:

```bash
tox -e sanity-py3.11-2.14,unit-py3.11-2.14 --ansible
```

To run all tests of a specific type in all available environments, use the factor `-f` flag:

```bash
tox -f unit --ansible -p auto
```

To run all tests across all available environments:

```bash
tox --ansible -p auto
```

Note: The `-p auto` flag will run multiple tests in parallel.
Note: The specific python interpreter will need to be pre-installed on you system, e.g.:

```bash
sudo dnf install python3.9
```

## Configuration

`tox-ansible` can be configured using the `tox.ini` file. The following options are available:

```ini
[ansible]
skip =
    2.10
    2.11
```

This will skip tests in any environment that uses ansible 2.10 or 2.11. The list of strings are used for a simply string in string comparison of environment names.

## Usage in a CI/CD pipeline

The repo contains a github workflow that can be used in a github actions CI/CD pipeline. The workflow will run all tests across all available environments, unless limited by the `skip` option in the `tox.ini` file.

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

## How does it work?

`tox` will, by default, create a python virtual environment for a given environment. `tox-ansible` adds ansible collection specific build and test logic to tox. The collection is copied into the virtual environment created by tox, built, and installed into the virtual environment. The installation of the collection will include the collection's collection dependencies. `tox-ansible` will also install any python dependencies from a `test-requirements.txt` and `requirements.txt` file. The virtual environment's temporary directory is used, so the copy, build and install steps are performed with each test run ensuring the current collection code is used.

`tox-ansible` also sets the `ANSIBLE_COLLECTIONS_PATHS` environment variable to point to the virtual environment's temporary directory. This ensures that the collection under test is used when running tests. The `pytest-ansible-units` pytest plugin injects the `ANSIBLE_COLLECTIONS_PATHS` environment variable into the collection loader so ansible-core can locate the collection.

`pytest` is ued to run both the `unit` and `integration tests`.
`ansible-test sanity` is used to run the `sanity` tests.

## License

MIT
