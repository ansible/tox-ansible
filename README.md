# tox-ansible

## Introduction

`tox-ansible` is a utility designed to simplify the testing of Ansible content collections.

Implemented as a `tox` plugin, `tox-ansible` provides a simple way to test Ansible content collections across multiple Python interpreters and Ansible versions.

`tox-ansible` uses familiar python testing tools to perform the actual testing. It uses `tox` to create and manage the testing environments, `ansible-test sanity` to run the sanity tests, and `pytest` to run the unit and integration tests. This eliminated the black box nature of other approaches and allowed for more control over the testing process.

When used on a local development system, each of the environments are left intact after a test run. This allows for easy debugging of failed tests for a given test type, python interpreter and Ansible version.

By using `tox` to create and manage the testing environments, Test outcomes should always be the same on a local development system as they are in a CI/CD pipeline.

`tox` virtual environments are created in the `.tox` directory. These are easily deleted and recreated if needed.

## Talk to us

Need help or want to discuss the project? See our [Contributor guide](https://ansible.readthedocs.io/projects/tox-ansible/contributor_guide/#talk-to-us) join the conversation!

## Installation

Install from pypi:

```bash
pip install tox-ansible
```

## Usage

From the root of your collection, add a `[tool.tox-ansible]` section to your `pyproject.toml`:

```toml
# pyproject.toml
[tool.tox]
requires = ["tox>=4.2"]

[tool.tox-ansible]
```

Then list the available environments:

```bash
tox list --ansible
```

A list of dynamically generated Ansible environments will be displayed:

```

default environments:
...
integration-py3.11-2.14      -> Integration tests for ansible.scm using ansible-core 2.14 and python 3.11
integration-py3.12-devel     -> Integration tests for ansible.scm using ansible-core devel and python 3.11
...
sanity-py3.11-2.14           -> Sanity tests for ansible.scm using ansible-core 2.14 and python 3.11
sanity-py3.12-devel          -> Sanity tests for ansible.scm using ansible-core devel and python 3.11
...
unit-py3.11-2.14             -> Unit tests for ansible.scm using ansible-core 2.14 and python 3.11
unit-py3.12-devel            -> Unit tests for ansible.scm using ansible-core devel and python 3.11
```

These represent the available testing environments. Each denotes the type of tests that will be run, the Python interpreter used to run the tests, and the Ansible version used to run the tests.

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
Note: The specific Python interpreter will need to be pre-installed on your system, e.g.:

```bash
sudo dnf install python3.10
```

To review the specific commands and configuration for each of the integration, sanity, and unit factors:

```bash
tox config --ansible
```

Generate specific GitHub action matrix as per scope mentioned with `--matrix-scope`:

```bash
tox --ansible --gh-matrix --matrix-scope unit
```

> **Note:** If your project uses `tox-ansible.ini` instead of `pyproject.toml`, add `--conf tox-ansible.ini` to each command above.

## Configuration

`tox-ansible` is configured via a `[tool.tox-ansible]` section in `pyproject.toml`.
Set `downstream = true` to union AAP/cert ansible-core extras onto the upstream
matrix (see ADR-001). The `skip` keyword filters environments by substring match:

```toml
# pyproject.toml
[tool.tox-ansible]
coverage = true
downstream = true
skip = [
    "devel",
]
```

This will generate plugin coverage reports for unit test environments, include
AAP-supported cores such as 2.16/2.18 when `downstream` is enabled, and skip
tests in any environment whose name contains `devel`. The list of strings is
used for a simple string in string comparison of environment names.

Alternatively, if using a `tox-ansible.ini` file, configure the `[ansible]` section:

```ini
# tox-ansible.ini
[ansible]
coverage = true
downstream = true
skip =
    devel
```

Coverage is disabled by default and can also be enabled for a single invocation:

```bash
tox --ansible --coverage -e unit-py3.13-2.19
```

tox-ansible installs `pytest-cov` and generates the collection-specific coverage configuration automatically. Reports include eligible Python files below `plugins/` that the unit tests do not import, showing them with 0% coverage. Raw coverage data is stored separately inside each tox unit environment, so parallel environments produce independent reports rather than a combined matrix report. Use `--no-coverage` to override configuration that enables coverage.

See the [configuration guide] for details on overriding environment settings.

[configuration guide]: https://ansible.readthedocs.io/projects/tox-ansible/configuration/#overriding-the-configuration

## Release process

`tox-ansible` is released with [CalVer] scheme version numbers. The particular scheme we are using is `YY.MM.MICRO`, meaning that a release in March 2025 will be named `25.3.0`, and if a patch (ie, non-feature) release is required for that release, it will be named 25.3.1, even if it is released in April. The month will not increment until a new version with features or other significant changes is released. More details about calver release process can be seen [here].

[here]: https://ansible.readthedocs.io/projects/team-devtools/guides/calver/
[CalVer]: https://calver.org/

## Note to version 1.x users

Users of tox-ansible v1 should use the stable/1.x branch because the default branch is a rewrite of the plugin for tox 4.0+ which is not backward compatible with the old plugin.

Version 1 of the plugin had native support for molecule. Please see the "Running molecule scenarios" above for an alternative approach.

## License

MIT
